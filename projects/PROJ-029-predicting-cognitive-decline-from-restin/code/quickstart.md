# Quickstart: Predicting Cognitive Decline from Resting-State fMRI Network Topology

This document provides the execution order to reproduce the analysis pipeline.
Ensure all dependencies in `code/requirements.txt` are installed.
Ensure the dataset `ds000246` is available in `data/raw/ds000246` or that network access is available for download.

## Prerequisites
- Python 3.11+
- FSL (for `mcflirt` if running full preprocessing, though T018 is skipped in this minimal run if matrices exist)
- OpenNeuro CLI (optional, for download)

## Execution Order

1. **Data Gate**: Verify dataset availability.
 ```bash
 python code/00_data_gate.py
 ```

2. **Download and Filter**: Download raw data and filter for eligible subjects.
 ```bash
 python code/01_download_and_filter.py
 ```
 *Outputs*: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

3. **Preprocess and Parcellate**: (Skipped if matrices exist, otherwise requires FSL/nilearn)
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Outputs*: `data/processed/connectivity_matrices/`

4. **Compute Graph Metrics**: Calculate network topology features.
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Outputs*: `data/processed/graph_metrics.csv`

5. **Collinearity Check**: Standalone analysis of feature correlations.
 ```bash
 python code/08_collinearity_check.py
 ```
 *Outputs*: `data/processed/collinearity_report.json`

6. **Train Model**: Nested Cross-Validation training.
 ```bash
 python code/04_train_model.py
 ```
 *Outputs*: `data/processed/model.pkl`, `data/processed/performance_report.json` (initial)

7. **Evaluate Model**: Detailed evaluation metrics.
 ```bash
 python code/05_evaluate_model.py
 ```
 *Outputs*: `data/processed/performance_report.json` (final)

8. **Permutation Test**: Significance testing.
 ```bash
 python code/06_permutation_test.py
 ```
 *Outputs*: `data/processed/permutation_results.json`

9. **Sensitivity Analysis**: Threshold robustness.
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Outputs*: `data/processed/sensitivity_report.json`

10. **Generate Report**: Aggregate findings.
 ```bash
 python code/09_generate_report.py
 ```
 *Outputs*: `data/artifacts/final_report.md`

11. **Verify Success Criteria**: Check against thresholds.
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Outputs*: `data/artifacts/verification_status.txt`, `data/artifacts/runtime_report.json`