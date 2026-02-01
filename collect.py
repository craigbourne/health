import os
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from github import Github, Auth

# Load the token from .env file
load_dotenv()
token = os.getenv('GITHUB_TOKEN')

# Connect to GitHub
auth = Auth.Token(token)
g = Github(auth=auth)

# Read the list of repos
with open('repos.txt', 'r') as file:
    repos = [line.strip() for line in file if line.strip()]

# ==================== TIME PERIOD DEFINITIONS ====================
# Define 4 time periods for temporal analysis (6-month intervals over 24 months)
now = datetime.now(timezone.utc)

time_periods = {
    "period_1": {
        "name": "18-24 months ago",
        "start": now - timedelta(days=730),
        "end": now - timedelta(days=547)
    },
    "period_2": {
        "name": "12-18 months ago", 
        "start": now - timedelta(days=547),
        "end": now - timedelta(days=365)
    },
    "period_3": {
        "name": "6-12 months ago",
        "start": now - timedelta(days=365),
        "end": now - timedelta(days=183)
    },
    "period_4": {
        "name": "0-6 months ago (recent)",
        "start": now - timedelta(days=183),
        "end": now
    }
}

# Additional time reference for recent activity metrics
three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)

# ==================== HELPER FUNCTIONS ====================
def get_period_metrics(repo, start_date, end_date):
    """Get commits and code churn for a time period in single pass"""
    commit_count = 0
    total_additions = 0
    total_deletions = 0
    
    commits = repo.get_commits(since=start_date, until=end_date)
    for commit in commits:
        commit_count += 1
        stats = commit.stats
        total_additions += stats.additions
        total_deletions += stats.deletions
    
    return {
        "commit_count": commit_count,
        "additions": total_additions,
        "deletions": total_deletions,
        "total_changes": total_additions + total_deletions,
        "churn_rate": (total_additions + total_deletions) / commit_count if commit_count > 0 else 0
    }

def calculate_pr_metrics(repo, start_date, end_date):
    """Calculate PR merge times and patterns for a time period"""
    prs = repo.get_pulls(state='closed', sort='updated', direction='desc')
    
    merge_times = []
    merged_count = 0
    closed_without_merge = 0
    
    for pr in prs:
        # Only look at PRs updated in our time period
        if pr.updated_at < start_date:
            break
        if pr.updated_at > end_date:
            continue
            
        if pr.merged_at:
            # Calculate time from opened to merged (in hours)
            time_to_merge = (pr.merged_at - pr.created_at).total_seconds() / 3600
            merge_times.append(time_to_merge)
            merged_count += 1
        else:
            closed_without_merge += 1
    
    avg_merge_time = sum(merge_times) / len(merge_times) if merge_times else 0
    
    return {
        "merged_count": merged_count,
        "closed_without_merge": closed_without_merge,
        "avg_merge_time_hours": round(avg_merge_time, 2),
        "merge_times_sample": [round(t, 2) for t in merge_times[:5]]  # First 5 for inspection
    }

def calculate_issue_response_times(repo, start_date, end_date):
    """Calculate time to first response for issues in time period"""
    issues = repo.get_issues(state='all', since=start_date, sort='created', direction='desc')
    
    response_times = []
    issues_without_response = 0
    issues_counted = 0
    
    for issue in issues:
        # Only issues created in our time period
        if issue.created_at > end_date:
            continue
        if issue.created_at < start_date:
            break
            
        # Skip pull requests (GitHub treats them as issues)
        if issue.pull_request:
            continue
            
        issues_counted += 1
        comments = issue.get_comments()
        
        try:
            first_comment = comments[0]
            time_to_response = (first_comment.created_at - issue.created_at).total_seconds() / 3600
            response_times.append(time_to_response)
        except (IndexError, StopIteration):
            issues_without_response += 1
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    return {
        "issues_created": issues_counted,
        "issues_with_response": len(response_times),
        "issues_without_response": issues_without_response,
        "avg_response_time_hours": round(avg_response_time, 2),
        "response_times_sample": [round(t, 2) for t in response_times[:5]]
    }

def calculate_pr_review_metrics(repo, start_date, end_date):
    """Calculate PR review participation for time period"""
    prs = repo.get_pulls(state='all', sort='updated', direction='desc')
    
    total_reviewers = set()
    total_reviews = 0
    prs_with_reviews = 0
    prs_without_reviews = 0
    review_comments = 0
    
    for pr in prs:
        if pr.updated_at < start_date:
            break
        if pr.updated_at > end_date:
            continue
            
        # Get reviews for this PR
        reviews = pr.get_reviews()
        review_count = 0
        
        for review in reviews:
            review_count += 1
            total_reviews += 1
            if review.user:
                total_reviewers.add(review.user.login)
        
        # Count review comments
        review_comments += pr.review_comments
        
        if review_count > 0:
            prs_with_reviews += 1
        else:
            prs_without_reviews += 1
    
    total_prs = prs_with_reviews + prs_without_reviews
    
    return {
        "total_prs": total_prs,
        "prs_with_reviews": prs_with_reviews,
        "prs_without_reviews": prs_without_reviews,
        "unique_reviewers": len(total_reviewers),
        "total_reviews": total_reviews,
        "review_comments": review_comments,
        "avg_reviews_per_pr": round(total_reviews / total_prs, 2) if total_prs > 0 else 0
    }

def calculate_contributor_metrics(repo, periods_dict):
    """Calculate contributor growth and retention across all periods"""
    # Track contributors by period
    contributors_by_period = {}
    
    for period_key, period_data in periods_dict.items():
        contributors_set = set()
        commits = repo.get_commits(since=period_data["start"], until=period_data["end"])
        
        for commit in commits:
            if commit.author:
                contributors_set.add(commit.author.login)
        
        contributors_by_period[period_key] = contributors_set
    
    # Calculate metrics for each period
    metrics_by_period = {}
    period_keys = ["period_1", "period_2", "period_3", "period_4"]
    
    for i, period_key in enumerate(period_keys):
        current_contributors = contributors_by_period[period_key]
        
        # New contributors (not in any previous period)
        previous_all = set()
        for j in range(i):
            previous_all.update(contributors_by_period[period_keys[j]])
        
        new_contributors = current_contributors - previous_all
        
        # Retention (contributors who return from previous period)
        if i > 0:
            previous_period = contributors_by_period[period_keys[i-1]]
            retained = current_contributors & previous_period
            retention_rate = len(retained) / len(previous_period) if len(previous_period) > 0 else 0
        else:
            retention_rate = 0
        
        metrics_by_period[period_key] = {
            "total_contributors": len(current_contributors),
            "new_contributors": len(new_contributors),
            "retention_rate": round(retention_rate, 2)
        }
    
    return metrics_by_period

def calculate_bug_feature_metrics(repo, start_date, end_date):
    """Classify issues as bugs vs features and track closure rates"""
    issues = repo.get_issues(state='all', since=start_date, sort='created', direction='desc')
    
    bugs_opened = 0
    bugs_closed = 0
    features_opened = 0
    features_closed = 0
    other_issues = 0
    
    for issue in issues:
        if issue.created_at > end_date:
            continue
        if issue.created_at < start_date:
            break
            
        # Skip pull requests
        if issue.pull_request:
            continue
        
        # Check labels
        labels = [label.name.lower() for label in issue.labels]
        is_bug = any(term in label for label in labels for term in ['bug', 'defect', 'error'])
        is_feature = any(term in label for label in labels for term in ['feature', 'enhancement', 'improvement'])
        
        if is_bug:
            bugs_opened += 1
            if issue.state == 'closed':
                bugs_closed += 1
        elif is_feature:
            features_opened += 1
            if issue.state == 'closed':
                features_closed += 1
        else:
            other_issues += 1
    
    bug_closure_rate = bugs_closed / bugs_opened if bugs_opened > 0 else 0
    feature_closure_rate = features_closed / features_opened if features_opened > 0 else 0
    
    return {
        "bugs_opened": bugs_opened,
        "bugs_closed": bugs_closed,
        "bug_closure_rate": round(bug_closure_rate, 2),
        "features_opened": features_opened,
        "features_closed": features_closed,
        "feature_closure_rate": round(feature_closure_rate, 2),
        "other_issues": other_issues
    }

# Store all repo data
all_repo_data = []

# Get data for each repo
for repo_name in repos:
    print(f"Collected: {repo_name}...", end=" ")
    repo = g.get_repo(repo_name)
    
    # Create dictionary for repo
    repo_data = {
        "name": repo_name,
        "collection_date": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    }
    
    # ==================== EVOLVABILITY (20%) ====================
    created_date = repo.created_at
    repo_age_days = (datetime.now(timezone.utc) - created_date).days

    # Basic info
    repo_data["evolvability"] = {
        "created_date": created_date.strftime('%Y-%m-%d'),
        "age_days": repo_age_days,
        "stars": repo.stargazers_count,
        "forks": repo.forks_count,
        "watchers": repo.watchers_count
    }
    
    # ==================== VELOCITY (30%) ====================
    # Get commits
    commits = repo.get_commits()

    # Last commit date
    last_commit = commits[0]
    last_commit_date = last_commit.commit.author.date
    
    # Count commits in last 3 months (backwards compatible)
    recent_commit_count = 0
    for commit in commits:
        if commit.commit.author.date >= three_months_ago:
            recent_commit_count += 1
        else:
            break  # Stop when we hit older commits
    # Get commits and code churn per time period (combined for efficiency)
    period_metrics = {}
    for period_key, period_data in time_periods.items():
        period_metrics[period_key] = get_period_metrics(
            repo,
            period_data["start"],
            period_data["end"]
        )
    
    # Calculate PR merge velocity per time period
    pr_metrics_by_period = {}
    for period_key, period_data in time_periods.items():
        pr_metrics_by_period[period_key] = calculate_pr_metrics(
            repo,
            period_data["start"],
            period_data["end"]
        )

# Get release info
    releases = repo.get_releases()
    latest_release = None
    latest_release_date = None
    recent_releases = 0
    
    try:
        latest_release = releases[0]
        latest_release_date = latest_release.published_at.strftime('%Y-%m-%d')
        
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        for release in releases:
            if release.published_at >= one_year_ago:
                recent_releases += 1
            else:
                break
    except (IndexError, StopIteration):
        pass  # No releases, keep defaults as None/0
    
    # Build velocity data once
    repo_data["velocity"] = {
        "last_commit_date": last_commit_date.strftime('%Y-%m-%d'),
        "commits_last_3_months": recent_commit_count,
        "period_metrics": period_metrics,
        "pr_metrics_by_period": pr_metrics_by_period,
        "releases_last_year": recent_releases,
        "latest_release_date": latest_release_date
    }
    
    # ==================== COLLABORATION (25%) ====================
    # Get contributor info
    contributors = repo.get_contributors()
    total_contributors = contributors.totalCount
    
    # Count active contributors from recent commits
    active_contributors_set = set()
    for commit in repo.get_commits(since=three_months_ago):
        if commit.author:
            active_contributors_set.add(commit.author.login)
    
    active_contributors = len(active_contributors_set)
    
    # Calculate contributor growth and retention across periods
    contributor_metrics_by_period = calculate_contributor_metrics(repo, time_periods)
    
    # Calculate issue response times per time period
    issue_response_by_period = {}
    for period_key, period_data in time_periods.items():
        issue_response_by_period[period_key] = calculate_issue_response_times(
            repo,
            period_data["start"],
            period_data["end"]
        )
    
    # Calculate PR review participation per time period
    pr_review_by_period = {}
    for period_key, period_data in time_periods.items():
        pr_review_by_period[period_key] = calculate_pr_review_metrics(
            repo,
            period_data["start"],
            period_data["end"]
        )
    
    # Get pull request info
    open_prs = repo.get_pulls(state='open').totalCount
    closed_prs = repo.get_pulls(state='closed').totalCount
    
    repo_data["collaboration"] = {
        "total_contributors": total_contributors,
        "active_contributors_last_3_months": active_contributors,
        "contributor_metrics_by_period": contributor_metrics_by_period,
        "pull_requests_open": open_prs,
        "pull_requests_closed": closed_prs,
        "issue_response_by_period": issue_response_by_period,
        "pr_review_by_period": pr_review_by_period
    }
    
    # ==================== QUALITY (25%) ====================
    # Count closed issues in last 3 months
    closed_issues = repo.get_issues(state='closed', since=three_months_ago).totalCount
    
    # Calculate bug vs feature metrics per time period
    bug_feature_by_period = {}
    for period_key, period_data in time_periods.items():
        bug_feature_by_period[period_key] = calculate_bug_feature_metrics(
            repo,
            period_data["start"],
            period_data["end"]
        )
    
    repo_data["quality"] = {
        "issues_open": repo.open_issues_count,
        "issues_closed_last_3_months": closed_issues,
        "bug_feature_by_period": bug_feature_by_period
    }
    
    # Add to collection
    all_repo_data.append(repo_data)
    print("✓")

# Save to JSON file
with open('repo_data.json', 'w') as f:
    json.dump(all_repo_data, f, indent=2)

print("-" * 50)
print(f"Data saved to repo_data.json")
print(f"Total repos collected: {len(all_repo_data)}")