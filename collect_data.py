import os
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

# Print header
print("Collecting data from", len(repos), "repos...")
print("-" * 60)

# Get data for each repository
for repo_name in repos:
    repo = g.get_repo(repo_name)
    print(f"{repo_name}")
    print(f"  Stars: {repo.stargazers_count}")
    print(f"  Open Issues: {repo.open_issues_count}")
    print()