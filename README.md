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
1. Collect data from GitHub (takes 10-20 minutes for detailed metrics)
2. Classify each repository based on activity patterns
3. Generate summary report

**Note:** Collection takes longer than simple metrics tools because it analyses historical patterns across 24 months.

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

GitHub allows 5,000 authenticated API requests per hour. This tool uses approximately 50-100 requests per repository depending on project size and activity level.