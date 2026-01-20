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

# Calculate date 3 months ago (with timezone)
three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)

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
    
    # Count commits in last 3 months
    recent_commit_count = 0
    for commit in commits:
        if commit.commit.author.date >= three_months_ago:
            recent_commit_count += 1
        else:
            break  # Stop when we hit older commits
    
    # Get release info
    releases = repo.get_releases()
    try:
        latest_release = releases[0]
        latest_release_date = latest_release.published_at.strftime('%Y-%m-%d')
        
        # Count releases in last year
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        recent_releases = 0
        for release in releases:
            if release.published_at >= one_year_ago:
                recent_releases += 1
            else:
                break
        
        repo_data["velocity"] = {
            "last_commit_date": last_commit_date.strftime('%Y-%m-%d'),
            "commits_last_3_months": recent_commit_count,
            "releases_last_year": recent_releases,
            "latest_release_date": latest_release_date
        }
    except (IndexError, StopIteration):
        repo_data["velocity"] = {
            "last_commit_date": last_commit_date.strftime('%Y-%m-%d'),
            "commits_last_3_months": recent_commit_count,
            "releases_last_year": 0,
            "latest_release_date": None
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