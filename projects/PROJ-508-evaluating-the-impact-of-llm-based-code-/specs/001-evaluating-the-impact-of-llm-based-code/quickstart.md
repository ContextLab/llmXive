# Quickstart: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Prerequisites
-   Python 3.11+
-   `pip` (Python package installer)
-   GitHub API rate limit awareness (no auth token required for public data, but limits apply).

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Step 1: Data Ingestion
Run the ingestion script to fetch GitHub data and compute metrics.
```bash
python code/ingest.py
```
-   **Output**: `data/derived/master_dataset.csv`, `data/raw/` (JSON files).
-   **Note**: This step may take a moderate duration due to API rate limits and retry logic.

### Step 2: Statistical Analysis
Run the analysis script to perform regressions and sensitivity checks.
```bash
python code/analyze.py
```
-   **Output**: `data/derived/regression_results.csv`, `data/derived/sensitivity_results.csv`.
-   **Note**: This step is fast (< 5 minutes).

### Step 3: Report Generation
Generate the final figures and report.
```bash
python code/report.py
```
-   **Output**: `docs/output/` (contains `effect_sizes.png`, `sensitivity.png`, `final_report.html`).

## Verification
To verify the pipeline:
1.  Check that `data/derived/master_dataset.csv` has at least 10 rows (repositories).
2.  Check that `docs/output/final_report.html` contains a forest plot and explicit associational framing.
3.  Run `pytest tests/` to ensure unit tests pass.

## Troubleshooting
-   **API Rate Limit**: If ingestion fails with a client error, wait 60 seconds and retry. The script implements exponential backoff.
-   **Missing Data**: If a repository has no PRs, it is automatically excluded.