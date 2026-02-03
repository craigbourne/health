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
    """Classify repo using temporal patterns from sophisticated metrics"""
    
    # Extract key metrics
    velocity = repo["velocity"]["period_metrics"]
    collaboration = repo["collaboration"]["contributor_metrics_by_period"]
    
    # Calculate velocity trend (comparing recent vs old periods)
    recent_commits = velocity["period_4"]["commit_count"]
    old_commits = velocity["period_1"]["commit_count"]
    
    # Calculate contributor trend
    recent_contributors = collaboration["period_4"]["total_contributors"]
    old_contributors = collaboration["period_1"]["total_contributors"]
    
    # Get recency
    last_commit = repo["velocity"]["last_commit_date"]
    last_commit_date = datetime.strptime(last_commit, '%Y-%m-%d')
    days_since_commit = (datetime.now() - last_commit_date).days
    
    # Build evidence dynamically
    evidence_parts = []
    evidence_parts.append(f"Recent commits: {recent_commits} vs {old_commits} (24mo ago)")
    evidence_parts.append(f"Recent contributors: {recent_contributors} vs {old_contributors} (24mo ago)")
    evidence_parts.append(f"Last commit: {days_since_commit} days ago")
    
    evidence = ", ".join(evidence_parts)
    
    # ABANDONED: Official statement OR completely dead
    if repo["name"] in official_statements:
        return "Abandoned", evidence
    
    if days_since_commit > 730 and recent_commits == 0:
        return "Abandoned", evidence
    
    # ACTIVE: Strong recent activity with growth or stability
    if recent_commits > 20 and days_since_commit < 30:
        if recent_commits >= old_commits * 0.8:  # Not declining significantly
            return "Active", evidence
    
    # DECLINING: Activity exists but trending downward
    if recent_commits > 0 and recent_commits < old_commits * 0.5:
        return "Declining", evidence
    
    if recent_commits > 0 and recent_commits <= 20:
        return "Declining", evidence
    
    # Default to abandoned if no clear pattern
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