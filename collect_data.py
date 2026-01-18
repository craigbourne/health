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
print("Collecting data from", len(repos), "repos...")
print("-" * 70)

# Get data for each repo
for repo_name in repos:
    print(f"Analysing: {repo_name}")
    repo = g.get_repo(repo_name)
    
    # Basic info
    print(f"  Stars: {repo.stargazers_count}")
    print(f"  Open Issues: {repo.open_issues_count}")
    
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
        print(f"  Latest Release: {latest_release_date.strftime('%Y-%m-%d')}")
        
        # Count releases in last year
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        recent_releases = 0
        for release in releases:
            if release.published_at >= one_year_ago:
                recent_releases += 1
            else:
                break
        
        print(f"  Releases (last year): {recent_releases}")
    except (IndexError, StopIteration):
        print(f"  Releases (last year): 0")
        print(f"  Latest Release: None")
    
    print()