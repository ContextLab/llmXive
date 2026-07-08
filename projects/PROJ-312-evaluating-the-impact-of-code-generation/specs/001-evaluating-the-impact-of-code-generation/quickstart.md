# Quickstart: Evaluating the Impact of Code Generation on Code Review Turnaround Time

## Prerequisites

- Python 3.11+
- GitHub Personal Access Token (with `public_repo` scope)
- 2 CPU cores, 7 GB RAM, 14 GB disk (GitHub Actions free-tier)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-312-evaluating-the-impact-of-code-generation
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variable**:
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```

## Running the Pipeline

### Step 1: Data Acquisition
```bash
python code/fetch_data.py
```
- Fetches top 10 Python/JS repos.
- Fetches PRs and commits.
- Classifies AI vs. Non-AI.
- Collects covariates (PR size, author activity).
- Outputs: `data/processed/prs_cleaned.csv`

### Step 1.5: Validation (Spot Check)
```bash
python code/validate_spot_check.py
```
- Generates a list of 50 random non-AI PRs for manual review.
- (Manual step required: review and label in `data/spot_check/validation_report.csv`).
- Outputs: `data/spot_check/validation_report.csv` (with `true_label` filled).

### Step 2: Statistical Analysis
```bash
python code/analyze.py
```
- Calculates descriptive statistics.
- Performs **Stratified Mann-Whitney U Test** (controls for PR size/author activity).
- Checks power (aborts if AI group < 30).
- Outputs: `data/processed/stats_summary.csv`

### Step 3: Visualization
```bash
python code/visualize.py
```
- Generates boxplot (IQR for whiskers only).
- Saves to `artifacts/boxplot.png` (≥300 DPI).

### Step 4: Report Generation
```bash
python code/report.py
```
- Assembles final report with statistics, plot, and limitations.
- **Conditional Logic**: If false-negative rate > 10%, injects limitation statement.
- Outputs: `artifacts/final_report.md`

## Verification

- **Check Data Quality**:
  ```bash
  grep -c "exclusion_reason" data/processed/prs_cleaned.csv
  ```
- **Verify Stratified Analysis**:
  ```bash
  grep "stratified" data/processed/stats_summary.csv
  ```
- **Confirm Plot Resolution**:
  ```bash
  identify -verbose artifacts/boxplot.png | grep "Density"
  ```

## Troubleshooting

- **API Rate Limit**:
  - Wait 15 minutes or use a different token.
  - Check logs for `403` responses.
- **Missing Data**:
  - Ensure `merged_at` is present for all PRs.
  - Check logs for exclusion reasons.
- **Small Sample**:
  - If AI group <30, check `data/processed/stats_summary.csv` for "ABORTED" flag.

## Next Steps

- Run `pytest` for unit tests.
- Review `artifacts/final_report.md` for findings.
- Submit results for review.
