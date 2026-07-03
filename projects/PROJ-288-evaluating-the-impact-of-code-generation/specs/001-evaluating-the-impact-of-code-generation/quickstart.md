# Quickstart: Evaluating the Impact of Code Generation on Code Review Time

## Prerequisites

-   Python 3.11+
-   GitHub Personal Access Token (with `public_repo` scope)
-   Git

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-288-evaluating-the-impact-of-code-generation
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Environment Variables**
    Create a `.env` file in the root directory:
    ```env
    GITHUB_TOKEN=your_github_personal_access_token
    GITHUB_RATE_LIMIT=5000
    ```

## Running the Pipeline

### 1. Data Extraction
Fetch PRs from high-star repositories with LLM keywords.
```bash
python code/main.py --action fetch --sample-size 100
```
*Output*: `data/raw/prs_YYYYMMDD.json`

### 2. Classification & Validation
Apply heuristics and generate validation logs.
```bash
python code/main.py --action classify --validation-sample 50
```
*Output*: `data/processed/prs_classified.parquet`, `data/validation_log.csv`

### 3. Statistical Analysis
Run the regression and non-parametric tests.
```bash
python code/main.py --action analyze
```
*Output*: `data/processed/metrics_summary.json`, `docs/reports/analysis_report.md`

### 4. Visualization
Generate plots.
```bash
python code/main.py --action viz
```
*Output*: `docs/reports/boxplot.png`, `docs/reports/scatter_plot.png`

## Testing

Run the unit and integration tests:
```bash
pytest tests/ -v
```

## Troubleshooting

-   **Rate Limit Exceeded**: Wait for the token bucket to refill or increase the `GITHUB_RATE_LIMIT` in the code if you have a higher tier token.
-   **Missing Timestamps**: The script automatically excludes PRs with missing `created_at` or `merged_at` timestamps. Check `data/processed/prs_clean.parquet` for `is_outlier` flags.
-   **Low Heuristic Accuracy**: If `validation_log.csv` shows Kappa < 0.6, the pipeline will halt. Manually review the `discrepancy` rows and adjust the heuristic thresholds in `code/config.py`.
