# Quickstart: Evaluating the Impact of Code Comment Style on Maintainability

## Prerequisites
*   Python 3.9+
*   `git` CLI installed
*   Network access to GitHub and HuggingFace
*   **Verified Dataset URL**: Ensure `codeparrot/github-code` (or alternative) is added to the `# Verified datasets` block in the project spec.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-032-evaluating-the-impact-of-code-comment-st
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `tree-sitter` and `pylint` require system dependencies. Ensure `gcc` and `python-dev` are installed.*

## Running the Pipeline

### 1. Data Acquisition (Fetch & Clone)
```bash
python code/fetch.py --target 500 --batch-size 10
```
*Output*: `data/raw/` populated with clones. `data/intermediate/repo_list.json` created.
*Note*: If no verified dataset URL is found, the script will exit with a BLOCKED status.

### 2. Metric Computation & Validation
```bash
python code/metrics.py --input data/intermediate/repo_list.json --output data/processed/metrics.csv
python code/validate_metrics.py --input data/processed/metrics.csv --output data/processed/validation_report.json
```
*Output*: `data/processed/metrics.csv` with all calculated metrics and `validation_report.json` with accuracy stats.

### 3. Statistical Analysis
```bash
python code/analysis.py --input data/processed/metrics.csv --output data/processed/results.json
```
*Output*: `data/processed/results.json` containing regression results, p-values, and the sensitivity analysis sweep.

### 4. Generate Report
```bash
python code/report.py --input data/processed/results.json --output report.md
```

## Verification
Run the test suite to ensure metric accuracy:
```bash
pytest tests/
```
*Check*: Ensure `SC-002` ([deferred] accuracy) passes on the validation set.

## Troubleshooting
*   **Memory Error**: Reduce `--batch-size` in `fetch.py`.
*   **Clone Failures**: Check network connectivity or GitHub rate limits. The script logs skipped repos.
*   **Pylint Errors**: Ensure `pylint` is installed and compatible with the target Python version.
*   **Dataset Blocked**: Verify that the `codeparrot/github-code` dataset (or alternative) has been added to the `# Verified datasets` block in the project specification.
