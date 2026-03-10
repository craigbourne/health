import json
from datetime import datetime

with open('repo_data.json') as f:
    repos = json.load(f)

for repo in repos:
    velocity = repo["velocity"]["period_metrics"]
    collaboration = repo["collaboration"]["contributor_metrics_by_period"]
    quality = repo["quality"]["bug_feature_by_period"]
    accumulation = repo["quality"]["issue_accumulation_by_period"]
    evolvability = repo["evolvability"]["refactoring_by_period"]
    
    # Extract key metrics
    p1_commits = velocity["period_1"]["commit_count"]
    p4_commits = velocity["period_4"]["commit_count"]
    
    p4_contributors = collaboration["period_4"]["total_contributors"]
    p1_contributors = collaboration["period_1"]["total_contributors"]
    retention = collaboration["period_4"]["retention_rate"]
    
    p4_bug_closure = quality["period_4"]["bug_closure_rate"]
    p4_accumulation = accumulation["period_4"]["accumulation_rate"]
    
    p4_refactoring = evolvability["period_4"]["refactoring_rate"]
    p4_dependencies = evolvability["period_4"]["dependency_update_rate"]
    
    last_commit = datetime.strptime(repo["velocity"]["last_commit_date"], '%Y-%m-%d')
    days_since = (datetime.now() - last_commit).days
    
    # Calculate trajectory
    if p1_commits > 0:
        trajectory = p4_commits / p1_commits
    else:
        trajectory = 1.0 if p4_commits > 0 else 0.0
    
    # Calculate contributor trend
    if p1_contributors > 0:
        contributor_trend = p4_contributors / p1_contributors
    else:
        contributor_trend = 1.0 if p4_contributors > 0 else 0.0
    
    # Quality health
    quality_healthy = p4_bug_closure > 0.6 and p4_accumulation < 0.4
    quality_moderate = p4_bug_closure > 0.3 or p4_accumulation < 0.6
    
    # Maintenance activity
    maintenance_active = (p4_refactoring + p4_dependencies) > 0.1
    
    evidence = (f"P4: {p4_commits} commits (trajectory: {trajectory:.2f}), "
                f"Contributors: {p4_contributors} (trend: {contributor_trend:.2f}), "
                f"Retention: {retention:.2f}, "
                f"Bug closure: {p4_bug_closure:.2f}, "
                f"Accumulation: {p4_accumulation:.2f}, "
                f"Maintenance: {p4_refactoring + p4_dependencies:.2f}, "
                f"Last: {days_since}d ago")
    
    # Classification logic using all metrics
    if p4_commits == 0 or days_since > 365:
        classification = "Abandoned"
    
    elif ((p4_commits > 80 or trajectory > 0.8) and 
          days_since < 60 and 
          (retention > 0.2 or contributor_trend >= 0.8)):
        classification = "Active"
    
    elif (p4_commits >= 20 and 
          trajectory >= 0.4 and 
          days_since < 120 and 
          retention > 0.15 and 
          maintenance_active):
        classification = "Moderate"
    
    elif (p4_commits >= 10 and 
          days_since < 180):
        classification = "Moderate"
    
    elif p4_commits >= 1 and days_since < 365:
        classification = "Declining"
    
    else:
        classification = "Declining"
    
    repo["classification"] = classification
    repo["classification_evidence"] = evidence

with open('repo_data.json', 'w') as f:
    json.dump(repos, f, indent=2)

print("✓ Classifications added to repo_data.json")