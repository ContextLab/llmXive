# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide outlines the steps to reproduce the analysis for PROJ-029.

## Prerequisites

- Python 3.11+
- Required dependencies installed via `pip install -r code/requirements.txt`
- OpenNeuro dataset `ds000246` availability (verified by T004c)

## Execution Order

Run the following commands in sequence from the project root:

1. **Data Ingestion & Filtering**
 ```bash
 python code/01_download_and_filter.py
 ```
 *Outputs*: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

2. **Preprocessing & Parcellation**
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Outputs*: `data/processed/connectivity_matrices/` (NIfTI or.npy files per subject)

3. **Graph Metric Computation**
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Outputs*: `data/processed/graph_metrics.csv`

4. **Collinearity Check (Standalone Report)**
 ```bash
 python code/08_collinearity_check.py
 ```
 *Outputs*: `data/processed/collinearity_report.json`

5. **Model Training**
 ```bash
 python code/04_train_model.py
 ```
 *Outputs*: `data/processed/model.pkl`, `data/processed/performance_report.json` (partial)

6. **Model Evaluation**
 ```bash
 python code/05_evaluate_model.py
 ```
 *Outputs*: `data/processed/performance_report.json` (final)

7. **Permutation Test**
 ```bash
 python code/06_permutation_test.py
 ```
 *Outputs*: `data/processed/permutation_results.json`

8. **Sensitivity Analysis**
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Outputs*: `data/processed/sensitivity_report.json`

9. **Report Generation**
 ```bash
 python code/09_generate_report.py
 ```
 *Outputs*: `data/artifacts/final_report.md`

10. **Success Criteria Verification**
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Outputs*: `data/artifacts/verification_status.txt`, `data/artifacts/runtime_report.json`

## Notes

- Ensure `code/requirements.txt` includes all necessary packages (nilearn, networkx, scikit-learn, pandas, numpy, psutil, joblib, scipy).
- The pipeline assumes sufficient RAM (7GB+) for graph metric computation.
- Random seeds are fixed to 42 for reproducibility.
- If any step fails, check the logs in `data/processed/` or `data/artifacts/` for specific error messages.