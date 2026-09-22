# Quickstart Guide

## Prerequisites
- Python 3.8+
- `pip install ucimlrepo pandas numpy scikit-learn statsmodels`

## Running the Pipeline

1. **Initialize Project Structure** (Optional if not done):
 ```bash
 python code/setup_project_structure.py
 ```

2. **Run the Main Pipeline**:
 This executes Ingestion (T012), Preprocessing (T013), Cohort (T014-T016), Models (T020-T023), Sensitivity (T027-T029), and Reporting (T024b-T025).
 ```bash
 python code/main_pipeline.py
 ```

3. **Verify Deliverables**:
 ```bash
 python code/quickstart_validator.py
 ```

## Expected Outputs
- `data/raw/cyberbullying_2021.csv`
- `data/results/analysis_cohort.csv`
- `data/results/regression_results.csv`
- `data/results/sensitivity_analysis.csv`
- `data/results/regression_summary.md`
- `data/results/platform_status.json`
- `data/results/validation_report.json`
