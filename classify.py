import json
from datetime import datetime

with open('repo_data.json') as f:
    repos = json.load(f)

for repo in repos:
    velocity = repo["velocity"]["period_metrics"]
    
    # Get P1 and P4 data
    p1_data = velocity.get("period_1", {})
    p4_data = velocity.get("period_4", {})
    
    p1_commits = p1_data.get("commit_count", 0)
    p4_commits = p4_data.get("commit_count", 0)
    
    last_commit = datetime.strptime(repo["velocity"]["last_commit_date"], '%Y-%m-%d')
    collection = datetime.strptime(repo["collection_date"], "%Y-%m-%d %H:%M:%S UTC")
    days_since = (collection - last_commit).days
    
    # Calculate trajectory if historical data exists
    if p1_commits > 0:
        trajectory = p4_commits / p1_commits
        evidence = f"P4: {p4_commits} commits, Trajectory: {trajectory:.2f}, Last: {days_since}d ago"
    else:
        trajectory = None
        evidence = f"P4: {p4_commits} commits, Last: {days_since}d ago (insufficient history for trajectory)"
    
    # Simple observable classification
    if p4_commits == 0 or days_since > 365:
        classification = "Abandoned"
    elif p4_commits > 80 and days_since < 90:
        classification = "Active"
    elif p4_commits >= 10 and days_since < 180:
        classification = "Moderate"
    elif p4_commits > 0 and days_since < 365:
        classification = "Declining"
    else:
        classification = "Abandoned"
    
    repo["classification"] = classification
    repo["classification_evidence"] = evidence

with open('repo_data.json', 'w') as f:
    json.dump(repos, f, indent=2)

print("✓ Classifications added to repo_data.json")