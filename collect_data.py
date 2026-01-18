import os
from dotenv import load_dotenv
from github import Github, Auth

# Load the token from .env file
load_dotenv()
token = os.getenv('GITHUB_TOKEN')

# Connect to GitHub (updated method)
auth = Auth.Token(token)
g = Github(auth=auth)

# Test: get info about one repository
repo = g.get_repo("vitejs/vite")

# Print some basic info
print("Repository:", repo.name)
print("Stars:", repo.stargazers_count)
print("Open Issues:", repo.open_issues_count)