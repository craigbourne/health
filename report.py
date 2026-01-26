import json
from datetime import datetime

# Load the data
with open('repo_data.json', 'r') as f:
    repos = json.load(f)

# Generate markdown report
report = []

# Header
report.append("# GitHub Repository Health - Validation Dataset")
report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"\n**Total Repositories:** {len(repos)}\n")

# Classification summary
classifications = {}
for repo in repos:
    status = repo.get('classification', 'Unknown')
    classifications[status] = classifications.get(status, 0) + 1

report.append("## Classification Summary\n")
for status, count in sorted(classifications.items()):
    report.append(f"- **{status}:** {count} repos")

# Detailed repo information
report.append("\n---\n")
report.append("## Repository Details\n")

for repo in repos:
    report.append(f"\n### {repo['name']}")
    report.append(f"\n**Classification:** {repo['classification']}")
    report.append(f"\n**Evidence:** {repo['classification_evidence']}")
    
    if 'official_statement' in repo:
        report.append(f"\n**Official Statement:** {repo['official_statement']}")
    
    # Evolvability metrics
    report.append(f"\n**Evolvability:**")
    report.append(f"- Created: {repo['evolvability']['created_date']}")
    report.append(f"- Age: {repo['evolvability']['age_days']} days")
    report.append(f"- Stars: {repo['evolvability']['stars']:,}")
    report.append(f"- Forks: {repo['evolvability']['forks']:,}")
    
    # Velocity metrics
    report.append(f"\n**Velocity:**")
    report.append(f"- Last Commit: {repo['velocity']['last_commit_date']}")
    report.append(f"- Commits (3 months): {repo['velocity']['commits_last_3_months']}")
    report.append(f"- Releases (year): {repo['velocity']['releases_last_year']}")
    
    # Collaboration metrics
    report.append(f"\n**Collaboration:**")
    report.append(f"- Total Contributors: {repo['collaboration']['total_contributors']}")
    report.append(f"- Active Contributors (3 months): {repo['collaboration']['active_contributors_last_3_months']}")
    report.append(f"- Open PRs: {repo['collaboration']['pull_requests_open']}")
    
    # Quality metrics
    report.append(f"\n**Quality:**")
    report.append(f"- Open Issues: {repo['quality']['issues_open']}")
    report.append(f"- Closed Issues (3 months): {repo['quality']['issues_closed_last_3_months']}")
    
    report.append("\n---")

# Save report
report_text = "\n".join(report)
with open('report.md', 'w') as f:
    f.write(report_text)

print("✓ Validation report generated: report.md")