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
    
    # Get pull request info
    open_prs = repo.get_pulls(state='open').totalCount
    closed_prs = repo.get_pulls(state='closed').totalCount
    
    repo_data["collaboration"] = {
        "total_contributors": total_contributors,
        "active_contributors_last_3_months": active_contributors,
        "pull_requests_open": open_prs,
        "pull_requests_closed": closed_prs
    }
    
    # ==================== QUALITY (25%) ====================
    # Count closed issues in last 3 months
    closed_issues = repo.get_issues(state='closed', since=three_months_ago).totalCount
    
    repo_data["quality"] = {
        "issues_open": repo.open_issues_count,
        "issues_closed_last_3_months": closed_issues
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