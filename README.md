# GitHub Repository Health Dashboard
Automated tool for assessing GitHub repository health through comprehensive metric collection and empirically validated scoring.

## What It Does
Collects 13 metrics from GitHub repositories across four 6-month periods (24 months total) and calculates a 0-100 health score. Repositories are classified into four health bands: Healthy (75-100), Moderate (50-74), Declining (25-49), or Critical (0-24).

The scoring algorithm was developed and validated against 12 repositories with known outcomes, achieving 100% classification accuracy.

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
git clone https://github.com/craigbourne/health
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

### Two-Step Workflow
**Step 1: Collect Data**
```bash
python3 collect.py
```

Fetches metrics from GitHub API and saves to `repo_data.json`. Collection time varies:
- Small repos: 10-20 minutes
- Large repos (e.g., Vite, Playwright): 30-45 minutes
- 10+ repo datasets: 4-6 hours total

The tool automatically handles GitHub API rate limits (5,000/hour primary, burst detection for secondary).

**Step 2: Score Repositories**
```bash
python3 score.py
```

Calculates health scores and displays results:

```
Repository Health Scores
---------------------------------------------------------------------------------------------------------
Repository                        Vel Collab   Qual   Evol    Raw  Trend  Bonus  Final  Band      
---------------------------------------------------------------------------------------------------------
vitejs/vite                      88.2   60.6   88.4   82.5   80.5    +10     +5   95.5  Healthy   
fastify/fastify                  77.3   78.9   94.0   74.5   81.5     +0     +5   86.5  Healthy   
gulpjs/gulp                       0.4   26.2   62.5    0.0   22.3     +0     +5   27.3  Declining 
```

## Output Files
- `repo_data.json` - Complete dataset with all metrics across four time periods

## Metrics Collected

### Velocity (35% weight)
**Why 35%:** Strongest discriminator between health categories. Active repos score 88-98%, declining 0-2%, abandoned 16-17%.

- Commit frequency per period (threshold: 90 commits)
- Code churn (threshold: 8,000 lines changed)
- PR merge time (threshold: 500 hours)

### Collaboration (25% weight)
- Contributor count (threshold: 20 contributors)
- Contributor retention rate (0-1 scale)
- PR review participation (threshold: 1.0 reviews/PR)
- Issue response time (threshold: 100 hours)

### Quality (25% weight)
- Bug closure rate (0-1 scale)
- Issue accumulation rate (inverted, 0-1 scale)
- Breaking change frequency (inverted, 0-1 scale)
- Regression rate (inverted, 0-1 scale)

**Note:** Abandoned repositories (no P4 commits AND no P3 OR >280 days inactive) score 0.1 on quality regardless of individual metrics.

### Evolvability (15% weight)
**Why 15%:** Weakest signal due to many zero values across all categories.

- Refactoring rate (threshold: 10% of commits)
- Dependency update rate (threshold: 20% of commits)
- Codebase growth (threshold: 3,000 net LOC)

**Note:** Abandoned repositories score 0.0 on evolvability.

## Time Periods
Data is collected across four 6-month periods:

- **Period 1:** 18-24 months ago
- **Period 2:** 12-18 months ago
- **Period 3:** 6-12 months ago
- **Period 4:** 0-6 months ago (most recent)

This temporal structure enables trend detection (comparing P4 vs P1) and identification of declining vs abandoned trajectories.

## Scoring Algorithm

### Base Score Calculation
```
raw_score = (velocity × 0.35 + collaboration × 0.25 + quality × 0.25 + evolvability × 0.15) × 100
```

### Modifiers
**Trend Bonus (+10 points):**
Awarded if Period 4 commits ≥ Period 1 commits × 1.2 (indicates growth)

**Recency Bonus (+5 points):**
Awarded if last commit <30 days ago AND Period 4 commits >0 (indicates active maintenance)

### Final Score
```
final_score = min(100, max(0, raw_score + trend_bonus + recency_bonus))
```

### Classification Bands
| Band | Score Range | Interpretation |
|------|-------------|----------------|
| **Healthy** | 75-100 | Active development, healthy metrics |
| **Moderate** | 50-74 | Stable but some concerns |
| **Declining** | 25-49 | Reduced activity, fading engagement |
| **Critical** | 0-24 | Abandoned or severely neglected |

## Sampling Methodology
For large repositories with thousands of issues/PRs, the tool uses stratified sampling to maintain reasonable collection times whilst preserving statistical validity:

**Full Collection:**
- All commits (required for accurate velocity/trend detection)
- All contributors
- All releases

**Sampled Collection (300 items per period):**
- Issues/PRs for collaboration and quality metrics
- Recency-weighted: most recently updated first

**Statistical Justification:**
- Sample size (300/period, ~75/period across 4 periods) exceeds Cohen's (1988) power analysis requirements for detecting medium effect sizes
- Exceeds Central Limit Theorem threshold (n≥30) for normal approximation
- Follows precedent from Mockus et al. (2002) and Nagappan & Ball (2005)

## Validation
The algorithm was validated against 12 repositories with documented outcomes:

| Category | Repositories | Accuracy |
|----------|-------------|----------|
| Active (Healthy) | vite, fastify, playwright, shadcn-ui | 4/4 (100%) |
| Declining | gulp, grunt | 2/2 (100%) |
| Abandoned (Critical) | coffeescript, knockout, atom, angular.js, bower, backbone | 6/6 (100%) |

**Overall: 12/12 (100%)**

See `algorithm_development_final.md` for detailed development process and methodological discussion.

## Project Structure
```
health/
├── collect.py                        # Data collection from GitHub API
├── score.py                          # Health scoring algorithm
├── repos.txt                         # List of repositories to analyse
├── repo_data.json                    # Output: collected metrics
├── algorithm_development_final.md    # Development process documentation
└── README.md                         # This file
```

## GitHub API Considerations
**Rate Limits:**
- Primary limit: 5,000 requests/hour (authenticated)
- Secondary limit: Burst detection (tool includes automatic backoff)

**Request Volumes:**
- Small repos: 1,000-2,000 requests
- Large repos: 5,000-7,000 requests

The tool automatically handles rate limit exhaustion by pausing and resuming when limits reset.

## Threshold Reference
Quick reference for interpretation:

| Metric | Excellent | Good | Concerning |
|--------|-----------|------|------------|
| Commits/period | 90+ | 30-89 | <30 |
| Contributors | 20+ | 10-19 | <10 |
| Reviews/PR | 1.0+ | 0.5-0.9 | <0.5 |
| Bug closure | 80%+ | 50-79% | <50% |
| Days since commit | <30 | 30-280 | >280 |
