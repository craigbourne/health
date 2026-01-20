import json
from datetime import datetime, timedelta

# Load the collected data
with open('repo_data.json', 'r') as f:
    repos = json.load(f)

# Known official statements for abandoned repos
official_statements = {
    "atom/atom": "https://github.blog/2022-06-08-sunsetting-atom/",
    "angular/angular.js": "https://blog.angular.io/discontinued-long-term-support-for-angularjs-cc066b82e65a",
    "bower/bower": "https://bower.io/blog/2017/how-to-migrate-away-from-bower/"
}

# Define classification rules based on proposal criteria
def classify_repo(repo):
    """Classify repo as Active, Declining, or Abandoned based on metrics"""
    
    commits = repo["velocity"]["commits_last_3_months"]
    releases = repo["velocity"]["releases_last_year"]
    active_contributors = repo["collaboration"]["active_contributors_last_3_months"]
    last_commit = repo["velocity"]["last_commit_date"]
    
    # Calculate days since last commit
    last_commit_date = datetime.strptime(last_commit, '%Y-%m-%d')
    days_since_commit = (datetime.now() - last_commit_date).days
    
    # Build evidence string from actual data
    evidence_parts = []
    
    if commits > 0:
        evidence_parts.append(f"{commits} commits in last 3 months")
    else:
        evidence_parts.append("No commits in last 3 months")
    
    if releases > 0:
        evidence_parts.append(f"{releases} releases in last year")
    else:
        evidence_parts.append("No releases in last year")
    
    evidence_parts.append(f"last commit {days_since_commit} days ago")
    
    if active_contributors > 0:
        evidence_parts.append(f"{active_contributors} active contributors")
    
    evidence = ", ".join(evidence_parts)
    
    # Apply classification criteria from proposal
    
    # ABANDONED: Official deprecation OR completely dead (2+ years no commits)
    if repo["name"] in official_statements:
        return "Abandoned", evidence
    
    if days_since_commit > 730 and commits == 0:  # 2 years
        return "Abandoned", evidence
    
    # ACTIVE: Regular commits in last 3 months, recent activity
    if commits > 20 and days_since_commit < 30:
        return "Active", evidence
    
    # DECLINING: Reduced activity - some commits OR inactive <2 years
    if commits > 0 and commits <= 20:
        return "Declining", evidence
    
    if commits == 0 and days_since_commit <= 730:
        return "Declining", evidence
    
    # Default: abandoned if completely inactive
    return "Abandoned", evidence

# Classify each repo
for repo in repos:
    status, evidence = classify_repo(repo)
    repo["classification"] = status
    repo["classification_evidence"] = evidence
    
    # Add official statement if exists
    if repo["name"] in official_statements:
        repo["official_statement"] = official_statements[repo["name"]]

# Save updated data
with open('repo_data.json', 'w') as f:
    json.dump(repos, f, indent=2)

print("✓ Classifications added to repo_data.json")
print("\nClassification summary:")
print(f"  Active: {sum(1 for r in repos if r.get('classification') == 'Active')}")
print(f"  Declining: {sum(1 for r in repos if r.get('classification') == 'Declining')}")
print(f"  Abandoned: {sum(1 for r in repos if r.get('classification') == 'Abandoned')}")