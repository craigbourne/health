import os
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

# Print header
print("Printing data from", len(repos), "repos...")
print("-" * 50)

# Get data for each repo
for repo_name in repos:
    print(f"Analysing: {repo_name}")
    repo = g.get_repo(repo_name)


    # ==================== EVOLVABILITY (20%) ====================
    created_date = repo.created_at
    repo_age_days = (datetime.now(timezone.utc) - created_date).days
    
    # Basic info
    print(f"  Created: {created_date.strftime('%Y-%m-%d')}")
    print(f"  Age (days): {repo_age_days}")
    print(f"  Stars: {repo.stargazers_count}")
    print(f"  Forks: {repo.forks_count}")
    print(f"  Watchers: {repo.watchers_count}")


    # ==================== VELOCITY (30%) ====================
    # Get commits
    commits = repo.get_commits()

    # Last commit date
    last_commit = commits[0]
    last_commit_date = last_commit.commit.author.date
    
    print(f"  Last Commit: {last_commit_date.strftime('%Y-%m-%d')}")
    
    # Count commits in last 3 months
    recent_commit_count = 0
    for commit in commits:
        if commit.commit.author.date >= three_months_ago:
            recent_commit_count += 1
        else:
            break  # Stop when we hit older commits
    
    print(f"  Commits (last 3 months): {recent_commit_count}")
    
    # Get release info
    releases = repo.get_releases()
    try:
        latest_release = releases[0]
        latest_release_date = latest_release.published_at
        
        # Count releases in last year
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        recent_releases = 0
        for release in releases:
            if release.published_at >= one_year_ago:
                recent_releases += 1
            else:
                break
        
        print(f"  Releases (last year): {recent_releases}")
        print(f"  Latest Release: {latest_release_date.strftime('%Y-%m-%d')}")
    except (IndexError, StopIteration):
        print(f"  Releases (last year): 0")
        print(f"  Latest Release: None")


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
    
    print(f"  Total Contributors: {total_contributors}")
    print(f"  Active Contributors (last 3 months): {active_contributors}")
    
    # Get pull request info
    open_prs = repo.get_pulls(state='open').totalCount
    closed_prs = repo.get_pulls(state='closed').totalCount
    
    print(f"  Pull Requests Open: {open_prs}")
    print(f"  Pull Requests Closed: {closed_prs}")


    # ==================== QUALITY (25%) ====================
    print(f"  Issues Open: {repo.open_issues_count}")
    
    # Count closed issues in last 3 months
    closed_issues = repo.get_issues(state='closed', since=three_months_ago).totalCount
    print(f"  Issues Closed (last 3 months): {closed_issues}")
    
    print()