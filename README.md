# GitHub Repository Health Dashboard
Automated tool for collecting and analysing GitHub repository health metrics.

## What It Does
Collects 13 metrics across 4 categories (Evolvability, Velocity, Collaboration, Quality) from GitHub repositories and classifies them as Active, Declining, or Abandoned.

## Requirements
- Python 3.13+ (check with `python3 --version`)
- GitHub account

## Setup

### 1. Get a GitHub Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it: `Dissertation Dashboard`
4. Set expiration: 90 days
5. Check only: `public_repo`
6. Generate and copy the token (starts with `ghp_`)

### 2. Clone This Repository
```bash
git clone <your-repo-url>
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

### Collect and Classify Data
Run complete pipeline:
```bash
python3 run.py
```

This will:
1. Fetch data from GitHub for all repos in `repos.txt`
2. Classify each repo as Active, Declining, or Abandoned
3. Save results to `repo_data.json`

### Individual Scripts
```bash
python3 collect.py   # Only collect data from GitHub
python3 classify.py  # Only classify (requires existing repo_data.json)
python3 print.py     # Print data to terminal (debugging)
python3 report.py    # Generate markdown summary report
```

## Output Files
- `repo_data.json` - Complete data with metrics and classifications
- `report.md` - Human-readable summary report

## Project Structure
```
health/
├── collect.py      # Fetches repo data from GitHub API
├── classify.py     # Applies classification rules
├── print.py        # Displays data in terminal
├── report.py       # Generates summary report
├── run.py          # Runs collection + classification
├── repos.txt       # List of repositories to analyse
├── repo_data.json  # Output: collected data
└── report.md       # Output: summary report
```

## Metrics Collected
**Evolvability (20%):** Created date, age, stars, forks, watchers  
**Velocity (30%):** Last commit, commits (3mo), releases (1yr)  
**Collaboration (25%):** Contributors, active contributors, PRs  
**Quality (25%):** Open issues, closed issues (3mo)

## Classification Criteria
**Active:** 20+ commits in 3 months, recent activity  
**Declining:** 1-20 commits OR inactive <2 years  
**Abandoned:** Official deprecation OR no commits 2+ years