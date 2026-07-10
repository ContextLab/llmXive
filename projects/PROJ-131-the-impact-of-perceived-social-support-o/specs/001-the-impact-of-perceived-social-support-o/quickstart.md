# Quickstart: The Impact of Perceived Social Support on Resilience to Online Harassment

## Prerequisites
*   Python 3.11+
*   Git
*   Access to the raw dataset (Cyberbullying Survey) placed in `data/raw/`.

## 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Preparation
**Important**: The raw data file must be present in `data/raw/`.
*   `data/raw/cyberbullying_survey.csv`

If this file is missing, the pipeline will fail with `E-MISSING-001`.

## 3. Run the Pipeline
Execute the full analysis pipeline:
```bash
python code/main_pipeline.py
```

This script will:
1.  Ingest and validate the Cyberbullying Survey data.
2.  Calculate mental health scores (CES-D, GAD-7, PCL-5).
3.  Construct the Analysis Cohort (single dataset).
4.  Fit robust regression models with bootstrapped CIs.
5.  Run sensitivity analyses.
6.  Generate `results/regression_results.csv` and `reports/summary.md`.

## 4. Verify Results
Check the output files:
*   `data/analysis/analysis_cohort.csv`: Verify `weight` column is not present (single dataset) and `NaN` values are minimal in critical columns.
*   `results/regression_results.csv`: Look for `interaction_coefficient` and `interaction_ci_lower/upper`.
*   `reports/vif_check.csv`: Ensure VIF values are < 5 for all predictors.

## 5. Troubleshooting
*   **Error E-MISSING-001**: The required dataset file (`cyberbullying_survey.csv`) or variables (e.g., PCL-5 items) were not found. The pipeline will skip the PTSD model and continue with Depression/Anxiety.
*   **Convergence Issues**: If OLS fails to converge, the pipeline falls back to standard OLS (without robust SEs) and logs a warning.