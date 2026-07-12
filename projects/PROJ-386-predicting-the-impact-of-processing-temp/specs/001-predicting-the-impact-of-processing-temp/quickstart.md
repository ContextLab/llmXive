# Quickstart: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

## Prerequisites

*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI) or a local environment with 7GB+ RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-386-predicting-the-impact-of-processing-temp
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Dependencies include: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `seaborn`.*

## Running the Pipeline

### Option 1: Local Execution (Small Sample)

To test the pipeline locally without downloading the full dataset (or if the dataset is small):

```bash
# Set random seed for reproducibility
export PYTHONHASHSEED=42

# Run the main pipeline
python code/main.py --sample-size 100 --timeout 3600
```
*Note: `--sample-size` is useful for debugging. The full run will use the entire available dataset.*

### Option 2: Full Run (CI/Local)

```bash
python code/main.py
```

This will:
1.  **Check Environment**: Verify CPU availability and set timeout.
2.  **Ingest Data**: Attempt to download and validate `nomad_structure_hf.csv`.
3.  **Preprocess**: Generate interaction features, normalize, and compute residuals.
4.  **Train**: Run Linear Regression (on residuals) and Random Forest (with grid search).
5.  **Analyze**: Generate collinearity and sensitivity reports.
6.  **Output**: Save artifacts to `data/artifacts/`.

### Expected Output

*   `data/processed/engineered_data.csv`: The clean dataset (with residuals).
*   `artifacts/baseline_model.pkl`: Linear regression model (on residuals).
*   `artifacts/rf_model.pkl`: Random Forest model (on residuals).
*   `artifacts/final_metrics.json`: R², MAE, and improvement metrics.
*   `artifacts/collinearity_report.json`: Flags for correlated predictors.
*   `stdout`: Progress logs and final summary.

## Troubleshooting

*   **"Critical variables missing from all sources"**: The verified datasets (NOMAD, etc.) do not contain the required `rolling_temperature` or `grain_size` columns. The pipeline correctly halted. This is a valid scientific outcome.
*   **"Timeout Enforced"**: The grid search took too long. The system fell back to default parameters. Check `artifacts/fallback_triggered.txt`.
*   **Memory Error**: The dataset is too large for 7GB RAM. The code includes chunking logic, but if it fails, reduce the dataset size or increase local RAM.

## Verification

Run the test suite to ensure contract compliance:

```bash
pytest tests/ -v
```

This verifies:
*   Schema validation logic.
*   Feature engineering correctness.
*   Timeout enforcement.
*   Model output schema compliance.