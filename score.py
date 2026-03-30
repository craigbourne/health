import json
from datetime import datetime, timezone

# ==================== CONFIGURATION ====================
CATEGORY_WEIGHTS = {
    "velocity": 0.35,      # Increased - strongest signal
    "collaboration": 0.25,
    "quality": 0.25,
    "evolvability": 0.15   # Decreased - weakest signal
}

# ==================== HELPERS ====================
def normalise_higher(value, cap):
    """Higher = better. Returns 0-1."""
    return min(1.0, value / cap) if cap > 0 else 0.0

def normalise_lower(value, cap):
    """Lower = better. Returns 1.0 at 0."""
    return max(0.0, 1.0 - (value / cap)) if cap > 0 else 1.0

def handle_zero(count, score_fn):
    """Return 0.5 for zero count (neutral when no data)."""
    return 0.5 if count == 0 else score_fn()

def get_days_since_last_commit(repo):
    """Days since last commit (calculated from collection date)."""
    last = datetime.strptime(repo["velocity"]["last_commit_date"], "%Y-%m-%d")
    collection = datetime.strptime(repo["collection_date"], "%Y-%m-%d %H:%M:%S UTC")
    return (collection - last).days

def is_abandoned(repo):
    """Abandoned: no P4 commits AND (no P3 OR >280 days inactive)."""
    p4 = repo["velocity"]["period_metrics"]["period_4"]["commit_count"]
    p3 = repo["velocity"]["period_metrics"]["period_3"]["commit_count"]
    days = get_days_since_last_commit(repo)
    return p4 == 0 and (p3 == 0 or days > 280)

# ==================== CATEGORY SCORING ====================
def score_velocity(repo):
    """Velocity: commits, churn, merge time (35%)"""
    p4v = repo["velocity"]["period_metrics"]["period_4"]
    p4pr = repo["velocity"]["pr_metrics_by_period"]["period_4"]

    # Lower thresholds to boost Active repos
    commit_score = normalise_higher(p4v["commit_count"], 90)
    churn_score = normalise_higher(p4v["total_changes"], 8000)
    merge_score = handle_zero(
        p4pr["merged_count"],
        lambda: normalise_lower(p4pr["avg_merge_time_hours"], 500)
    )

    return (commit_score + churn_score + merge_score) / 3

def score_collaboration(repo):
    """Collaboration: contributors, retention, reviews, response (25%)"""
    p4c = repo["collaboration"]["contributor_metrics_by_period"]["period_4"]
    p4r = repo["collaboration"]["pr_review_by_period"]["period_4"]
    p4i = repo["collaboration"]["issue_response_by_period"]["period_4"]

    contrib_score = normalise_higher(p4c["total_contributors"], 20)
    retention_score = p4c["retention_rate"]
    review_score = handle_zero(
        p4r["total_prs"],
        lambda: normalise_higher(p4r["avg_reviews_per_pr"], 1.0)
    )
    response_score = handle_zero(
        p4i["issues_created"],
        lambda: normalise_lower(p4i["avg_response_time_hours"], 100)
    )

    return (contrib_score + retention_score + review_score + response_score) / 4

def score_quality(repo):
    """Quality: bugs, accumulation, breaking changes, regressions (25%)"""
    if is_abandoned(repo):
        return 0.1

    p4b = repo["quality"]["bug_feature_by_period"]["period_4"]
    p4a = repo["quality"]["issue_accumulation_by_period"]["period_4"]
    p4br = repo["quality"]["breaking_changes_by_period"]["period_4"]
    p4rg = repo["quality"]["regression_by_period"]["period_4"]

    bug_score = handle_zero(p4b["bugs_opened"], lambda: p4b["bug_closure_rate"])
    accum_score = 1.0 - min(1.0, p4a["accumulation_rate"])
    break_score = 1.0 - min(1.0, p4br["breaking_change_rate"])
    reg_score = 1.0 - min(1.0, p4rg["regression_rate"])

    return (bug_score + accum_score + break_score + reg_score) / 4

def score_evolvability(repo):
    """Evolvability: refactoring, dependencies, growth (15%)"""
    if is_abandoned(repo):
        return 0.0
    
    p4rf = repo["evolvability"]["refactoring_by_period"]["period_4"]
    p4g = repo["evolvability"]["feature_growth_by_period"]["period_4"]

    refactor_score = normalise_higher(p4rf["refactoring_rate"], 0.10)
    dep_score = normalise_higher(p4rf["dependency_update_rate"], 0.20)
    growth_score = normalise_higher(max(0, p4g["net_loc_change"]), 3000)

    return (refactor_score + dep_score + growth_score) / 3

# ==================== MODIFIERS ====================
def calculate_trend_modifier(repo):
    """Reward growth: P4 >= P1 × 1.2 → +10 points. Adapts to available data."""
    p4 = repo["velocity"]["period_metrics"]["period_4"]["commit_count"]
    
    # Try P1 first (full 24-month comparison)
    p1 = repo["velocity"]["period_metrics"].get("period_1", {}).get("commit_count", None)

    if p1 is not None:
        # Full trajectory available
        if p1 == 0:
            return 10 if p4 > 0 else 0
        return 10 if (p4 / p1) >= 1.2 else 0

    # Fall back to P3 (12-month comparison) if P1 unavailable
    p3 = repo["velocity"]["period_metrics"].get("period_3", {}).get("commit_count", None)

    if p3 is not None:
        # Partial trajectory available
        if p3 == 0:
            return 10 if p4 > 0 else 0
        return 10 if (p4 / p3) >= 1.2 else 0

    # No historical data - no trend bonus
    return 0

def calculate_recency_bonus(repo):
    """Recent activity bonus: commit in last 30 days AND >0 commits → +5 points."""
    days = get_days_since_last_commit(repo)
    p4_commits = repo["velocity"]["period_metrics"]["period_4"]["commit_count"]

    if days < 30 and p4_commits > 0:
        return 5
    return 0

# ==================== LEHMAN'S LAWS DIAGNOSTICS ====================
def calculate_self_regulation(repo):
    """Law 3: Self-regulating evolution shows consistent patterns.

    Returns bonus/penalty based on commit consistency:
    CV < 0.3 (consistent) → +3
    CV > 0.6 (erratic) → -3
    Otherwise → 0
    """
    periods = repo["velocity"]["period_metrics"]

    # Collect commit counts from available periods
    commits = []
    for period in ["period_1", "period_2", "period_3", "period_4"]:
        if period in periods:
            commits.append(periods[period]["commit_count"])

    # Need at least 2 periods to calculate variance
    if len(commits) < 2:
        return 0

    mean = sum(commits) / len(commits)

    # Can't calculate CV if mean is zero
    if mean == 0:
        return 0

    # Calculate coefficient of variation
    variance = sum((x - mean) ** 2 for x in commits) / len(commits)
    std_dev = variance ** 0.5
    cv = std_dev / mean

    # Convert to bonus/penalty
    if cv < 0.3:
        return 3  # Consistent evolution
    elif cv > 0.6:
        return -3  # Erratic patterns
    else:
        return 0  # Neutral

def calculate_org_stability(repo):
    """Law 4: Stable organisations maintain consistent team sizes.

    Returns bonus/penalty based on contributor stability:
    CV < 0.3 (stable) → +3
    CV > 0.6 (unstable) → -3
    Otherwise → 0
    """
    collab = repo["collaboration"]["contributor_metrics_by_period"]

    # Collect contributor counts from available periods
    contributors = []
    for period in ["period_1", "period_2", "period_3", "period_4"]:
        if period in collab:
            contributors.append(collab[period]["total_contributors"])

    # Need at least 2 periods
    if len(contributors) < 2:
        return 0

    mean = sum(contributors) / len(contributors)

    if mean == 0:
        return 0

    # Calculate coefficient of variation
    variance = sum((x - mean) ** 2 for x in contributors) / len(contributors)
    std_dev = variance ** 0.5
    cv = std_dev / mean

    # Convert to bonus/penalty
    if cv < 0.3:
        return 3  # Stable team
    elif cv > 0.6:
        return -3  # High turnover
    else:
        return 0  # Neutral

def calculate_high_activity_bonus(repo):
    """Reward exceptionally active projects (>500 commits P4).

    Recognizes projects with very high development activity.
    Examples: vite (593), playwright (1071), meteor (805)
    """
    p4_commits = repo["velocity"]["period_metrics"]["period_4"]["commit_count"]
    return 5 if p4_commits > 500 else 0

def calculate_maintenance_mode_penalty(repo):
    """Penalize legacy projects in maintenance mode.

    Pattern: Low activity + High quality + No growth = Legacy maintenance

    Detects projects like jQuery: technically sound but minimal development,
    no growth trajectory, market has moved on.

    Criteria: <60 commits P4, quality >75, no trend bonus
    """
    p4_commits = repo["velocity"]["period_metrics"]["period_4"]["commit_count"]
    quality_score = score_quality(repo) * 100
    trend = calculate_trend_modifier(repo)

    # Pattern: Low activity, high quality, no growth
    if p4_commits < 60 and quality_score > 75 and trend == 0:
        return -30
    return 0

# ==================== BAND CLASSIFICATION ====================
def get_band(score):
    """Map score to health band."""
    if score >= 75:
        return "Healthy"
    elif score >= 50:
        return "Moderate"
    elif score >= 25:
        return "Declining"
    else:
        return "Critical"

# ==================== MAIN SCORING ====================
def score_repo(repo):
    """Calculate overall health score."""
    vel = score_velocity(repo)
    collab = score_collaboration(repo)
    qual = score_quality(repo)
    evol = score_evolvability(repo)

    raw = (
        vel * CATEGORY_WEIGHTS["velocity"] +
        collab * CATEGORY_WEIGHTS["collaboration"] +
        qual * CATEGORY_WEIGHTS["quality"] +
        evol * CATEGORY_WEIGHTS["evolvability"]
    ) * 100

    trend = calculate_trend_modifier(repo)
    recency = calculate_recency_bonus(repo)

    # Lehman's Laws modifiers
    self_reg = calculate_self_regulation(repo)
    org_stab = calculate_org_stability(repo)

    # Activity and maintenance modifiers
    high_activity = calculate_high_activity_bonus(repo)
    maintenance_penalty = calculate_maintenance_mode_penalty(repo)

    final = max(0, min(100, raw + trend + recency + self_reg + org_stab + high_activity + maintenance_penalty))

    return {
        "velocity_score": round(vel * 100, 1),
        "collaboration_score": round(collab * 100, 1),
        "quality_score": round(qual * 100, 1),
        "evolvability_score": round(evol * 100, 1),
        "self_regulation": self_reg,
        "org_stability": org_stab,
        "high_activity": high_activity,
        "maintenance_penalty": maintenance_penalty,
        "trend_modifier": trend,
        "recency_bonus": recency,
        "raw_score": round(raw, 1),
        "health_score": round(final, 1),
        "health_band": get_band(round(final, 1))
    }

# ==================== TEST ====================
if __name__ == "__main__":
    with open('repo_data.json') as f:
        repos = json.load(f)

    print("Repository Health Scores")
    print("-" * 125)
    print(f"{'Repository':<20} {'Vel':>6} {'Collab':>6} {'Qual':>6} {'Evol':>6} {'SelfReg':>8} {'OrgStab':>8} {'HiAct':>6} {'Maint':>6} {'Raw':>6} {'Trend':>6} {'Recncy':>6} {'Final':>6}  {'Band':<10}")
    print("-" * 125)

    for repo in repos:
        scores = score_repo(repo)

        # Format diagnostic values as bonus/penalty
        self_reg_str = f"{scores['self_regulation']:+d}" if scores['self_regulation'] != 0 else "0"
        org_stab_str = f"{scores['org_stability']:+d}" if scores['org_stability'] != 0 else "0"
        hi_act_str = f"{scores['high_activity']:+d}" if scores['high_activity'] != 0 else "0"
        maint_str = f"{scores['maintenance_penalty']:+d}" if scores['maintenance_penalty'] != 0 else "0"

        # Extract repo name (after slash)
        repo_name = repo['name'].split('/')[-1]

        print(f"{repo_name:<20} "
            f"{scores['velocity_score']:>6.1f} "
            f"{scores['collaboration_score']:>6.1f} "
            f"{scores['quality_score']:>6.1f} "
            f"{scores['evolvability_score']:>6.1f} "
            f"{self_reg_str:>8} "
            f"{org_stab_str:>8} "
            f"{hi_act_str:>6} "
            f"{maint_str:>6} "
            f"{scores['raw_score']:>6.1f} "
            f"{scores['trend_modifier']:>+6.0f} "
            f"{scores['recency_bonus']:>+6.0f} "
            f"{scores['health_score']:>6.1f}  "
            f"{scores['health_band']:<10}")

    print("-" * 125)