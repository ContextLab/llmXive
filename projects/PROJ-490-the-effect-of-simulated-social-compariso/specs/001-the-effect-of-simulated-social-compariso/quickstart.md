# Quickstart: Simulated Social Comparison on Self-Esteem in VR

## Prerequisites
-   Python 3.11+
-   Git
-   Access to GitHub Actions (for CI execution) or a local CPU environment.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-490-the-effect-of-simulated-social-compariso
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions compatible with CPU-only execution (e.g., `scikit-learn`, `statsmodels`).*

## Running the Pipeline

### 1. Data Generation / Discovery
Run the data loader script. It will attempt to find real data (and fail, triggering synthetic generation) or generate synthetic data if configured.
```bash
python code/data_loader.py --mode synthetic --seed 42 --n 200
```
*Output*: `data/raw/synthetic_dataset.csv`

### 2. Preprocessing (MICE)
Handle missing values and compute change scores.
```bash
python code/preprocessing.py --input data/raw/synthetic_dataset.csv --output data/processed/cleaned_imputed.csv
```
*Output*: `data/processed/cleaned_imputed.csv`

### 3. Statistical Analysis
Fit the regression model, validate assumptions, and run bootstraps.
```bash
python code/analysis.py --input data/processed/cleaned_imputed.csv --output data/outputs/regression_results.json --bootstrap 1000
```
*Output*: `data/outputs/regression_results.json` (coefficients, p-values, diagnostics).

### 4. Sensitivity Analysis
Run threshold sweeps, power analysis, and missingness mechanism diagnostics.
```bash
python code/sensitivity.py --input data/outputs/regression_results.json --output data/outputs/sensitivity_report.json
```

## Verification
To ensure the pipeline works:
1.  Check that `data/outputs/regression_results.json` contains a `parameter_recovery_bias` close to `0` (for synthetic data with β=0.2).
2.  Verify that `shapiro_p` > 0.05 and `breusch_pagan_p` > 0.05 in the output.
3.  Confirm that `vif_max` < 5.
4.  For synthetic data, ensure the `is_preliminary` flag is `false` (as power is deterministic in the synthetic path and not the success metric).

## Troubleshooting
-   **ImportError**: Ensure `requirements.txt` was installed in the active virtual environment.
-   **Memory Error**: Reduce `--n` in data generation or `--bootstrap` iterations. The default settings are optimized for typical RAM configurations.
-   **Missing Data**: If real data is used and missingness > 20%, the script will exclude rows per FR-002.