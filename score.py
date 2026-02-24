import json

# ==================== CONFIGURATION ====================
CATEGORY_WEIGHTS = {
    "velocity": 0.30,
    "collaboration": 0.25,
    "quality": 0.25,
    "evolvability": 0.20
}

# ==================== NORMALISATION ====================
def normalise_higher(value, cap):
    """Higher values = better health. Caps at threshold."""
    return min(1.0, value / cap) if cap > 0 else 0.0

def normalise_lower(value, cap):
    """Lower values = better health. Returns 1.0 at zero."""
    return max(0.0, 1.0 - (value / cap)) if cap > 0 else 1.0

def handle_zero(count, score_fn):
    """Return 0.5 when count is zero (no data vs poor performance)."""
    return 0.5 if count == 0 else score_fn()

# ==================== CATEGORY SCORING ====================
def score_velocity(repo):
    """Velocity: commits, churn, PR merge time (30%)"""
    period_4_velocity = repo["velocity"]["period_metrics"]["period_4"]
    period_4_prs = repo["velocity"]["pr_metrics_by_period"]["period_4"]

    commit_score = normalise_higher(period_4_velocity["commit_count"], 300)
    churn_score = normalise_higher(period_4_velocity["total_changes"], 20000)
    merge_score = handle_zero(
        period_4_prs["merged_count"],
        lambda: normalise_lower(period_4_prs["avg_merge_time_hours"], 168)
    )

    return (commit_score + churn_score + merge_score) / 3

def score_collaboration(repo):
    """Collaboration: contributors, retention, reviews, response time (25%)"""
    period_4_contributors = repo["collaboration"]["contributor_metrics_by_period"]["period_4"]
    period_4_reviews = repo["collaboration"]["pr_review_by_period"]["period_4"]
    period_4_issues = repo["collaboration"]["issue_response_by_period"]["period_4"]

    contributor_score = normalise_higher(period_4_contributors["total_contributors"], 20)
    retention_score = period_4_contributors["retention_rate"]
    review_score = handle_zero(
        period_4_reviews["total_prs"],
        lambda: normalise_higher(period_4_reviews["avg_reviews_per_pr"], 3)
    )
    response_score = handle_zero(
        period_4_issues["issues_created"],
        lambda: normalise_lower(period_4_issues["avg_response_time_hours"], 168)
    )

    return (contributor_score + retention_score + review_score + response_score) / 4

def score_quality(repo):
    """Quality: bug closure, issue accumulation, breaking changes, regressions (25%)"""
    period_4_bugs = repo["quality"]["bug_feature_by_period"]["period_4"]
    period_4_accumulation = repo["quality"]["issue_accumulation_by_period"]["period_4"]
    period_4_breaking = repo["quality"]["breaking_changes_by_period"]["period_4"]
    period_4_regressions = repo["quality"]["regression_by_period"]["period_4"]

    bug_score = handle_zero(
        period_4_bugs["bugs_opened"],
        lambda: period_4_bugs["bug_closure_rate"]
    )
    accumulation_score = 1.0 - min(1.0, period_4_accumulation["accumulation_rate"])
    breaking_score = 1.0 - min(1.0, period_4_breaking["breaking_change_rate"])
    regression_score = 1.0 - min(1.0, period_4_regressions["regression_rate"])

    return (bug_score + accumulation_score + breaking_score + regression_score) / 4

def score_evolvability(repo):
    """Evolvability: refactoring, dependencies, codebase growth (20%)"""
    period_4_refactoring = repo["evolvability"]["refactoring_by_period"]["period_4"]
    period_4_growth = repo["evolvability"]["feature_growth_by_period"]["period_4"]

    refactoring_score = period_4_refactoring["refactoring_rate"]
    dependency_score = period_4_refactoring["dependency_update_rate"]
    growth_score = normalise_higher(max(0, period_4_growth["net_loc_change"]), 10000)

    return (refactoring_score + dependency_score + growth_score) / 3

# ==================== TEST ====================
if __name__ == "__main__":
    with open('repo_data.json', 'r') as f:
        repos = json.load(f)
    
    test_repo = repos[0]
    print(f"Repository: {test_repo['name']}\n")
    print(f"Velocity:      {score_velocity(test_repo) * 100:5.1f}")
    print(f"Collaboration: {score_collaboration(test_repo) * 100:5.1f}")
    print(f"Quality:       {score_quality(test_repo) * 100:5.1f}")
    print(f"Evolvability:  {score_evolvability(test_repo) * 100:5.1f}")