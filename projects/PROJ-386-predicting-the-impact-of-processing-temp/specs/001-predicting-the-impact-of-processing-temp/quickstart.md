# Quickstart: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

## Prerequisites
*   Python 3.10+
*   Git
*   Access to the GitHub Actions runner (or local environment with 2+ CPU cores).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-386-predicting-the-impact-of-processing-temp
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The entire pipeline is orchestrated by `code/main.py`.

### 1. Data Ingestion & Validation
This step attempts to download and validate data. If data is missing, it exits with code 1.
```bash
python code/main.py --step download
```
*   **Output**: `data/processed/cleaned_data.csv` (if successful) or `artifacts/error.json` (if failed).
*   **Expected Behavior**: If the NOMAD dataset lacks `rolling_temperature` or `process_type`, the script will halt and print: `{"code": "E_DATA_MISSING", ...}`.

### 2. Feature Engineering & Baseline Modeling
Generates interaction features, filters by process type, and trains the linear baseline.
```bash
python code/main.py --step baseline
```
*   **Output**: `artifacts/baseline_model.pkl`, `artifacts/baseline_metrics.json`.
*   **Note**: If N < 100, this step will skip the non-linear modeling phase.

### 3. Non-Linear Modeling (with Timeout Fallback)
Trains the Random Forest with grid search. Includes a 4-hour timeout.
```bash
python code/main.py --step non_linear
```
*   **Output**: `artifacts/non_linear_model.pkl`, `artifacts/non_linear_metrics.json`.
*   **Note**: Only runs if N >= 100. If the process exceeds 4 hours, it automatically switches to default parameters.

### 4. Sensitivity & Diagnostics
Runs sensitivity analysis, collinearity checks, and confounder analysis (including E-value calculation).
```bash
python code/main.py --step diagnostics
```
*   **Output**: `artifacts/sensitivity_report.json`, `artifacts/collinearity_report.json`, `artifacts/confounder_report.json`.

### 5. Versioning & Hashing
Computes SHA-256 hashes for all artifacts and updates the state file.
```bash
python code/main.py --step hash
```
*   **Output**: Updates `state/projects/PROJ-386-...yaml` with `artifact_hashes`.

## Verifying Results
To ensure reproducibility, run the full pipeline:
```bash
python code/main.py --step full
```
Check `artifacts/reports/summary.md` for the final R² delta, stability metrics, and E-value.