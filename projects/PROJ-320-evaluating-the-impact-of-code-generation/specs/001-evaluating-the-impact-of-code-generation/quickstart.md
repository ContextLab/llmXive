# Quickstart: Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

## Prerequisites

*   Python 3.11+
*   GitHub Personal Access Token (optional, for higher rate limits)
*   `pip`

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Install dependencies**:
    ```bash
    cd projects/PROJ-320-evaluating-the-impact-of-code-generation/code
    pip install -r requirements.txt
    ```
3.  **Set environment variables** (optional):
    ```bash
    export GITHUB_TOKEN=your_token_here
    ```

## Running the Pipeline

### Step 1: Data Acquisition
Fetch PRs from the prioritized list of repositories.
```bash
python data/fetch_github.py --output data/raw/prs_raw.json
```
*This script handles batching, rate limiting, and fallback repositories automatically.*

### Step 2: Classification & Metric Extraction
Classify PRs and compute metrics (including temporal covariates).
```bash
python data/classify_prs.py --input data/raw/prs_raw.json --output data/processed/prs_labeled.csv
python data/extract_metrics.py --input data/processed/prs_labeled.csv --output data/processed/prs_metrics.csv
```

### Step 3: Statistical Analysis
Run **Mann-Whitney U tests** (primary) and t-tests (sensitivity).
```bash
python analysis/statistical_tests.py --input data/processed/prs_metrics.csv --output reports/results.json
python analysis/visualizations.py --input data/processed/prs_metrics.csv --output reports/figures/
```

### Step 4: Sensitivity Analysis (FR-008)
Re-run analysis using only the secondary-detector-confirmed cohort.
```bash
python analysis/sensitivity_analysis.py --input data/processed/prs_metrics.csv --output reports/sensitivity_results.json
```

### Step 5: Manual Audit (Required)
Generate the audit sample for manual validation.
```bash
python audit/manual_validation.py --input data/processed/prs_metrics.csv --output data/processed/audit_log.csv
```
*Note: You must manually review the `audit_log.csv` and update the `human_ground_truth` column. The `detector_score` column is recorded for comparison (per SC-004).*

## Verification

*   **Checksums**: Verify `data/` file checksums match `state/` records.
*   **Audit Rate**: Ensure `audit_log.csv` error rate (Human vs. Primary Signature) is < 5%.
*   **Reproducibility**: Re-run the pipeline; results should match (within floating point tolerance) if seeds are pinned.
