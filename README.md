# GitHub Repository Health Dashboard

Automated tool for assessing GitHub repository health through metric collection and validated scoring.

## What It Does

Collects metrics from GitHub repositories and calculates a 0-100 health score with four health bands: Healthy (75-100), Moderate (50-74), Declining (25-49) or Critical (0-24).

The tool adapts to available data, working with projects from 6 weeks to 6+ years old. Mature projects receive full trajectory analysis whilst younger projects are scored on current metrics.

## How It Works

The tool applies Lehman's Laws of Software Evolution to measure repository health:

**Continuing Change** (Velocity metrics)
Software must continuously adapt or become less useful. The tool measures commit frequency, code churn and PR merge times to detect whether development is active or stagnating.

**Increasing Complexity** (Quality metrics)
Complexity increases unless actively managed. The tool tracks bug closure rates, issue accumulation and breaking changes to identify quality degradation.

**Continuing Growth** (Evolvability metrics)
Functionality must grow to maintain user satisfaction. The tool measures refactoring rates, dependency updates and codebase growth to assess whether the project is evolving or stagnating.

**Collaboration Health** (Collaboration metrics)
Whilst not directly from Lehman, collaboration patterns predict sustainability. The tool tracks contributor retention, review participation and issue response times.

These four categories are weighted (Velocity 35%, Collaboration 25%, Quality 25%, Evolvability 15%) and combined into a single health score.

## What Data Gets Collected

The tool extracts the following data from GitHub's API:

**Commits** (all commits across 24 months)
- Author, timestamp, files changed
- Lines added/deleted
- Commit message (analysed for keywords: refactor, dependency, feature, bug fix)

**Pull Requests** (sampled: 300 per period for large repos)
- Open/merged/closed counts
- Merge times
- Review participation (who reviewed, how many reviews)

**Issues** (sampled: 300 per period for large repos)
- Creation and closure dates
- Labels (bug, feature, enhancement)
- Response times (time to first response)
- Reopening patterns (regression detection)

**Contributors**
- All unique contributors across periods
- Retention patterns (who stayed, who left)
- New contributor rates

**Releases**
- Version numbers, release dates
- Breaking change detection

**Codebase metrics**
- Total lines of code
- Net growth per period

This data is processed into 13 metrics across the four health categories, then scored.

## Use Cases

### 1. Dependency Assessment
Evaluate external open-source libraries before adoption. A declining or critical score indicates risk of unmaintained or abandoned code.

**When to use:** Before adding any external dependency to your project. Check health scores to avoid adopting libraries that may be abandoned.

**Example:** Compare health scores for `lodash` vs `ramda` before adding as dependencies.

**Data needed:** 24+ months for full trajectory analysis

### 2. Early Warning System  
Monitor your own project's health score over time. Declining scores signal problems: reduced contributor engagement, accumulating technical debt or velocity slowdown.

**When to use:** Regular health checks (monthly/quarterly) on active projects you own. Track trends to catch problems early.

**Example:** Your project scores 85 (Healthy) at 6 months but drops to 65 (Moderate) at 12 months.

**Data needed:** Any amount of history (scoring adapts)

### 3. Portfolio Monitoring
Compare health across multiple internal projects with varying maturity. Identify which need intervention.

**When to use:** Managing multiple projects and need to prioritise resources. Compare scores to identify struggling projects.

**Example:** Compare 5 projects: 3 score Healthy (80+), 1 Moderate (68), 1 Declining (35).

**Data needed:** Mix of project ages supported (scoring adapts per project)

## Requirements

- Python 3.13+
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

Never commit `.env` to git (already in `.gitignore`).

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

Fetches metrics from GitHub API and saves to `repo_data.json`. 

**Collection time varies significantly by repository size:**
- Small repos (few contributors, <1000 commits): 10-20 minutes
- Medium repos (moderate activity): 30-45 minutes  
- Large repos (vite, playwright, meteor): 1-3 hours each
- 10+ repo datasets: 4-8 hours total

**Why collection takes time:**
- The tool collects data across 24 months (4 periods)
- Each period requires separate API calls for commits, PRs, issues, contributors
- Large repos may have thousands of commits requiring individual API calls
- Sampling (300 items/period) reduces this but cannot eliminate wait times

**Progress indicators:**
The tool shows live progress:
```
Collecting: meteor/meteor
meteor/meteor: Processing commits: 15400...
meteor/meteor: ✓ Saved (3/10 repos)
```

**Reducing collection time:**
- Start with smaller repos to test the tool
- Use caffeinate on Mac to prevent sleep: `caffeinate -dims python3 collect.py`
- Run overnight for large datasets
- The tool saves after each repo completes (data preserved if interrupted)

The tool handles GitHub API rate limits (5,000/hour primary, burst detection for secondary) with automatic backoff and retry.

**Step 2: Score Repositories**

```bash
python3 score.py
```

Calculates health scores and displays results:

```
Repository Health Scores
--------------------------------------------------------------------------------------------------
Repository                  Expected   Vel Collab   Qual   Evol    Raw  Trend  Bonus  Final  Band
--------------------------------------------------------------------------------------------------
vitejs/vite                 Healthy   88.2   60.6   88.4   82.5   80.5    +10     +5   95.5  Healthy
fastify/fastify             Healthy   77.3   78.9   94.0   74.5   81.5     +0     +5   86.5  Healthy
gulpjs/gulp                Declining   0.4   26.2   62.5    0.0   22.3     +0     +5   27.3  Declining
```

**Understanding the output:**
- **Expected:** Ground truth classification (for validation only - requires classify.py)
- **Vel:** Velocity score (0-100) - commit frequency, churn, PR merge time
- **Collab:** Collaboration score (0-100) - contributors, retention, reviews
- **Qual:** Quality score (0-100) - bug closure, issue accumulation
- **Evol:** Evolvability score (0-100) - refactoring, dependencies, growth
- **Raw:** Weighted combination before modifiers (0-100)
- **Trend:** Bonus points for growth (+10 if P4 ≥ P1 × 1.2, else 0)
- **Bonus:** Recency bonus (+5 if last commit <30 days and P4 >0, else 0)
- **Final:** Total health score (0-100)
- **Band:** Health classification (Healthy/Moderate/Declining/Critical)

## Output Files

- `repo_data.json` - Complete dataset with all metrics across four time periods

## Metrics Collected

### Velocity (35% weight)

Strongest discriminator between health categories. Active repos score 88-98%, declining 0-2%, abandoned 16-17%.

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

Abandoned repositories (no P4 commits AND no P3 OR >280 days inactive) score 0.1 on quality regardless of individual metrics.

### Evolvability (15% weight)

Weakest signal due to many zero values across all categories.

- Refactoring rate (threshold: 10% of commits)
- Dependency update rate (threshold: 20% of commits)
- Codebase growth (threshold: 3,000 net LOC)

Abandoned repositories score 0.0 on evolvability.

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

### Adaptive Scoring

The tool adapts to available historical data:

**Mature Projects (24+ months):**
- Full analysis using all 4 periods
- Trend bonus compares P4 vs P1 (24-month trajectory)
- Complete trajectory assessment

**Intermediate Projects (12-18 months):**
- Partial trajectory using available periods
- Trend bonus compares P4 vs P3 (12-month trajectory)
- Adapts thresholds based on data availability

**Young Projects (<12 months):**
- Scores based on current metrics (P4 only)
- No trend bonus (insufficient historical data)
- Produces valid 0-100 health score

This ensures projects of any age can be assessed, with scoring adapting to available data rather than requiring 24 months of history.

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
| **Critical** | 0-24 | Abandoned or neglected |

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
- Sample size (300/period) exceeds Cohen's (1988) power analysis requirements for detecting medium effect sizes
- Exceeds Central Limit Theorem threshold (n≥30) for normal approximation
- Follows precedent from Mockus et al. (2002) and Nagappan & Ball (2005)

## Validation

The algorithm was validated against 22 repositories with documented outcomes.

| Category | Count | Examples | Accuracy |
|----------|-------|----------|----------|
| Active (Healthy) | 8 | vite, fastify, playwright, svelte, remix, astro, ember, shadcn-ui | 8/8 |
| Moderate | 3 | meteor, jquery, lodash | 3/3 |
| Declining | 2 | gulp, grunt | 2/2 |
| Abandoned (Critical) | 9 | coffeescript, knockout, atom, angular.js, bower, backbone, Polymer, moment, marionette | 9/9 |

**Overall: 22/22 (100%)**

See `algorithm_development_final.md` for detailed development process and methodological discussion.

## Troubleshooting

**Collection takes too long**
- Start with 2-3 small repos to test
- Run overnight for large datasets
- Use `caffeinate -dims python3 collect.py` on Mac to prevent sleep

**API rate limit errors**
- The tool handles this automatically with backoff
- Wait times shown in terminal (e.g., "Setting next backoff to 539s")
- Collection resumes when limits reset

**Repository too small (< 6 months history)**
- Tool will collect available data and score accordingly
- No trend bonus awarded (insufficient history)
- Still produces valid health score

**Collection interrupted**
- Data saved after each repo completes
- Restart collect.py - it skips already-collected repos
- Remove completed repos from repos.txt if needed

**Empty repo_data.json**
- File created but empty means collection crashed before first repo completed
- Check terminal for error messages
- Verify GitHub token is valid

## Project Structure

```
health/
├── collect.py                        # Data collection from GitHub API
├── classify.py                       # Ground truth labels (validation only)
├── score.py                          # Health scoring algorithm
├── repos.txt                         # List of repositories to analyse
├── repo_data.json                    # Output: collected metrics
├── algorithm_development_final.md    # Development process documentation
└── README.md                         # This file
```

**Note on classify.py:** This script creates ground truth classifications for validation purposes. Users do not need to run it unless conducting their own validation studies. The tool works with just `collect.py` and `score.py`.

## GitHub API Considerations

**Rate Limits:**
- Primary limit: 5,000 requests/hour (authenticated)
- Secondary limit: Burst detection (tool includes automatic backoff)

**Request Volumes:**
- Small repos: 1,000-2,000 requests
- Large repos: 5,000-7,000 requests

The tool handles rate limit exhaustion by pausing and resuming when limits reset.

## Threshold Reference

Quick reference for interpretation:

| Metric | Excellent | Good | Concerning |
|--------|-----------|------|------------|
| Commits/period | 90+ | 30-89 | <30 |
| Contributors | 20+ | 10-19 | <10 |
| Reviews/PR | 1.0+ | 0.5-0.9 | <0.5 |
| Bug closure | 80%+ | 50-79% | <50% |
| Days since commit | <30 | 30-280 | >280 |

## References

Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.

Mockus, A., Fielding, R. T. and Herbsleb, J. D. (2002). Two case studies of open source software development: Apache and Mozilla. *ACM Transactions on Software Engineering and Methodology*, 11(3), 309-346.

Nagappan, N. and Ball, T. (2005). Use of relative code churn measures to predict system defect density. *Proceedings of the 27th International Conference on Software Engineering*, 284-292.