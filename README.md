# GitHub Repository Health Dashboard

Automated tool for collecting and analysing GitHub repository health metrics.

## What It Does

Collects 13 metrics from GitHub repositories and tracks them across four 6-month periods covering the last 24 months. Classifies repositories as Active, Declining or Abandoned based on activity patterns over time.

## Requirements

- Python 3.13+ (check with `python3 --version`)
- GitHub account

## Setup

### 1. Get a GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name the token
4. Set expiration: 90 days
5. Check only: `public_repo`
6. Generate and copy the token (starts with `ghp_`)

### 2. Clone This Repository

```bash
git clone 
cd health
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
```

### 4. Install Dependencies

```bash
pip install PyGithub python-dotenv
```

### 5. Configure GitHub Token

Create a `.env` file:

```bash
touch .env
```

Add your token to `.env`:

```
GITHUB_TOKEN=ghp_your_token_here
```

**Important:** Never commit `.env` to git (already in `.gitignore`)

### 6. Add Repositories to Analyse

Edit `repos.txt` and add repository names (one per line):

```
vitejs/vite
fastify/fastify
your-org/your-repo
```

## Usage

### Run Complete Pipeline

```bash
python3 run.py
```

This will:
1. Collect data from GitHub
2. Classify each repository based on activity patterns
3. Generate summary report

**Collection time:** Varies by repository size and activity level. Small repos (e.g., bower, grunt) complete in 10-20 minutes. Large active repositories (e.g., Vite with 15,000+ commits) require 30-45 minutes. For validation datasets of 10+ repositories, expect 4-6 hours total. The script automatically handles GitHub's API rate limits by pausing and resuming collection as needed.

**Note:** Collection prioritises data completeness over speed. Comprehensive historical analysis across 24 months requires significantly more API requests than simple snapshot tools.

### Individual Scripts

```bash
python3 collect.py   # Collect data from GitHub
python3 classify.py  # Classify repositories (requires repo_data.json)
python3 report.py    # Generate markdown summary
```

## Output Files

- `repo_data.json` - Full dataset with metrics across four time periods
- `report.md` - Summary report showing trends and classifications

## Metrics Collected

### Velocity (30%)

- Commit frequency per period
- Code churn (lines added/deleted)
- PR merge time

### Collaboration (25%)

- Contributor growth rate
- Contributor retention
- PR review participation
- Issue response time

### Quality (25%)

- Bug closure rate
- Issue accumulation rate
- Breaking change frequency
- Regression rate

### Evolvability (20%)

- Refactoring frequency
- Dependency update rate
- Feature addition rate
- Codebase growth rate

## Time Periods

Data is collected across four 6-month periods:

- **Period 1:** 18-24 months ago
- **Period 2:** 12-18 months ago
- **Period 3:** 6-12 months ago
- **Period 4:** 0-6 months ago (recent)

This allows tracking of trends and identification of growth or decline patterns.

## Classification

**Active:** Recent activity with stable or growing metrics compared to historical periods

**Declining:** Reduced activity or declining contributor/commit numbers over time

**Abandoned:** Official deprecation statement or no activity for 2+ years

## Collection Approach

### Full Collection
- **Commits:** Complete historical data collected (required for accurate velocity and code churn metrics)
- **Contributors:** Full contributor history per period
- **Releases:** Complete release data

### Stratified Sampling (Large Repositories)
For repositories with extensive issue/PR histories (>300 items per period), sampling limits are applied:
- **Issues/PRs:** 300 items per 6-month period
- **Sample size justification:** Provides ~75 items per period, exceeding the Central Limit Theorem threshold (n≥30) for valid statistical inference and meeting Cohen's (1988) power analysis requirements for detecting medium effect sizes in proportion comparisons
- **Sampling method:** Most recent items first (sorted by update date), ensuring temporal relevance

This approach balances API efficiency with statistical validity, following precedent from software engineering research (Mockus et al., 2002; Nagappan & Ball, 2005).

### Small Repositories
Repositories with <300 issues/PRs per period receive full collection across all metrics, ensuring no data loss for projects where comprehensive analysis is feasible.

## Project Structure

```
health/
├── collect.py      # Fetches data from GitHub API
├── classify.py     # Classifies based on activity patterns
├── report.py       # Generates summary report
├── run.py          # Runs full pipeline
├── repos.txt       # List of repositories to analyse
├── repo_data.json  # Output: collected data
└── report.md       # Output: summary report
```

## GitHub API Limits

GitHub enforces a primary rate limit of 5,000 authenticated requests per hour, plus secondary limits preventing rapid successive requests to the same endpoint (burst detection).

**Request volume per repository:**
- Small repos (e.g., bower): ~1,000-2,000 requests
- Large active repos (e.g., Vite): ~5,000-7,000 requests

The collection script includes automatic rate limit management:
- **Primary limit exhaustion:** Pauses until hourly quota resets, then resumes automatically
- **Burst detection (403 errors):** 100ms delays between commit statistic retrievals prevent secondary rate limit violations

For datasets of 10+ repositories, collection may span multiple rate limit cycles. The script handles this transparently - simply leave it running overnight.

## References

- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.
- Mockus, A., Fielding, R. T., & Herbsleb, J. D. (2002). Two case studies of open source software development: Apache and Mozilla. *ACM Transactions on Software Engineering and Methodology*, 11(3), 309-346.
- Nagappan, N., & Ball, T. (2005). Use of relative code churn measures to predict system defect density. *Proceedings of the 27th International Conference on Software Engineering*, 284-292.
