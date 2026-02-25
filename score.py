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
    """Days since last commit."""
    last = datetime.strptime(repo["velocity"]["last_commit_date"], "%Y-%m-%d")
    last = last.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last).days

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
    """Reward growth: P4 >= P1 × 1.2 → +10 points."""
    p1 = repo["velocity"]["period_metrics"]["period_1"]["commit_count"]
    p4 = repo["velocity"]["period_metrics"]["period_4"]["commit_count"]

    if p1 == 0:
        return 10 if p4 > 0 else 0
    
    return 10 if (p4 / p1) >= 1.2 else 0

def calculate_recency_bonus(repo):
    """Recent activity bonus: commit in last 30 days AND >0 commits → +5 points."""
    days = get_days_since_last_commit(repo)
    p4_commits = repo["velocity"]["period_metrics"]["period_4"]["commit_count"]
    
    if days < 30 and p4_commits > 0:
        return 5
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
    final = max(0, min(100, raw + trend + recency))

    return {
        "velocity_score": round(vel * 100, 1),
        "collaboration_score": round(collab * 100, 1),
        "quality_score": round(qual * 100, 1),
        "evolvability_score": round(evol * 100, 1),
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
    print("-" * 105)
    print(f"{'Repository':<30} {'Vel':>6} {'Collab':>6} {'Qual':>6} {'Evol':>6} {'Raw':>6} {'Trend':>6} {'Bonus':>6} {'Final':>6}  {'Band':<10}  {'Expected':<10}")
    print("-" * 105)
    
    correct = 0
    for repo in repos:
        scores = score_repo(repo)
        expected = repo.get('classification', 'Unknown')
        
        expected_band = {
            'Active': 'Healthy',
            'Declining': 'Declining',
            'Abandoned': 'Critical'
        }.get(expected, 'Unknown')
        
        match = "✓" if scores['health_band'] == expected_band else "✗"
        if scores['health_band'] == expected_band:
            correct += 1
        
        print(f"{repo['name']:<30} "
              f"{scores['velocity_score']:>6.1f} "
              f"{scores['collaboration_score']:>6.1f} "
              f"{scores['quality_score']:>6.1f} "
              f"{scores['evolvability_score']:>6.1f} "
              f"{scores['raw_score']:>6.1f} "
              f"{scores['trend_modifier']:>+6.0f} "
              f"{scores['recency_bonus']:>+6.0f} "
              f"{scores['health_score']:>6.1f}  "
              f"{scores['health_band']:<10}  "
              f"{expected_band:<10} {match}")
    
    print("-" * 105)
    print(f"Accuracy: {correct}/12 ({100*correct/12:.1f}%)")