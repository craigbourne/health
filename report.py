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
report.append("\n---\n")

# Repository details
for repo in repos:
    report.append(f"\n### {repo['name']}")
    report.append(f"\n**Classification:** {repo['classification']}")
    report.append(f"\n**Evidence:** {repo['classification_evidence']}")
    
    if 'official_statement' in repo:
        report.append(f"\n**Official Statement:** {repo['official_statement']}")
    
    # Evolvability
    report.append(f"\n**Evolvability:**")
    report.append(f"- Created: {repo['evolvability']['created_date']}")
    report.append(f"- Age: {repo['evolvability']['age_days']} days")
    report.append(f"- Stars: {repo['evolvability']['stars']:,}")
    report.append(f"- Forks: {repo['evolvability']['forks']:,}")
    
    # Velocity trends
    report.append(f"\n**Velocity Trends:**")
    vm = repo['velocity']['period_metrics']
    report.append(f"- Commits: P1={vm['period_1']['commit_count']}, P2={vm['period_2']['commit_count']}, P3={vm['period_3']['commit_count']}, P4={vm['period_4']['commit_count']}")
    report.append(f"- Code churn (P4): {vm['period_4']['total_changes']:,} lines changed")
    report.append(f"- Churn rate (P4): {vm['period_4']['churn_rate']:.1f} lines/commit")
    
    # PR metrics
    prm = repo['velocity']['pr_metrics_by_period']['period_4']
    report.append(f"- PR merge time (P4): {prm['avg_merge_time_hours']}hrs average")
    report.append(f"- PRs merged (P4): {prm['merged_count']}")
    
    # Collaboration trends
    report.append(f"\n**Collaboration Trends:**")
    cm = repo['collaboration']['contributor_metrics_by_period']
    report.append(f"- Contributors: P1={cm['period_1']['total_contributors']}, P2={cm['period_2']['total_contributors']}, P3={cm['period_3']['total_contributors']}, P4={cm['period_4']['total_contributors']}")
    report.append(f"- New contributors (P4): {cm['period_4']['new_contributors']}")
    report.append(f"- Retention rate (P4): {cm['period_4']['retention_rate']:.0%}")
    
    # Issue response
    irm = repo['collaboration']['issue_response_by_period']['period_4']
    report.append(f"- Issue response time (P4): {irm['avg_response_time_hours']}hrs average")
    report.append(f"- Issues without response (P4): {irm['issues_without_response']}")
    
    # Quality metrics
    report.append(f"\n**Quality Metrics:**")
    bfm = repo['quality']['bug_feature_by_period']['period_4']
    report.append(f"- Bug closure rate (P4): {bfm['bug_closure_rate']:.0%}")
    report.append(f"- Bugs opened (P4): {bfm['bugs_opened']}")
    
    iam = repo['quality']['issue_accumulation_by_period']['period_4']
    report.append(f"- Issue accumulation (P4): {iam['net_accumulation']} net change")
    
    regm = repo['quality']['regression_by_period']['period_4']
    report.append(f"- Regression rate (P4): {regm['regression_rate']:.1%}")
    
    # Evolvability metrics
    report.append(f"\n**Evolvability Metrics:**")
    refm = repo['evolvability']['refactoring_by_period']['period_4']
    report.append(f"- Refactoring rate (P4): {refm['refactoring_rate']:.1%}")
    report.append(f"- Dependency updates (P4): {refm['dependency_commits']}")
    
    fgm = repo['evolvability']['feature_growth_by_period']['period_4']
    report.append(f"- Feature rate (P4): {fgm['feature_rate']:.1%}")
    report.append(f"- Net LOC growth (P4): {fgm['net_loc_change']:,} lines")
    
    report.append("\n---")

# Save report
report_text = "\n".join(report)
with open('report.md', 'w') as f:
    f.write(report_text)

print("✓ Validation report generated: report.md")