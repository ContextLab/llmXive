# Quickstart Guide

This guide outlines the execution order for the Predicting Cognitive Decline from Resting-State fMRI Network Topology pipeline.

## Prerequisites

- Python 3.11+
- Installed dependencies: `pip install -r code/requirements.txt`
- Access to OpenNeuro dataset `ds000246` (or local cache)

## Execution Order

Run the following commands in sequence from the project root:

1. **Data Ingestion and Filtering**
 ```bash
 python code/01_download_and_filter.py
 ```
 *Produces:* `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

2. **Preprocessing and Parcellation**
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Produces:* Adjacency matrices in `data/processed/adjacency_matrices/`

3. **Graph Metric Calculation**
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Produces:* `data/processed/graph_metrics.csv`

4. **Collinearity Check (Standalone Analysis)**
 ```bash
 python code/08_collinearity_check.py
 ```
 *Produces:* `data/processed/collinearity_report.json`
 *Note:* This script analyzes the full correlation matrix of the generated graph metrics.

5. **Model Training**
 ```bash
 python code/04_train_model.py
 ```
 *Produces:* `data/processed/model.pkl`, `data/processed/cv_results.json`

6. **Model Evaluation**
 ```bash
 python code/05_evaluate_model.py
 ```
 *Produces:* `data/processed/performance_report.json`

7. **Permutation Test**
 ```bash
 python code/06_permutation_test.py
 ```
 *Produces:* `data/processed/permutation_results.json`

8. **Sensitivity Analysis**
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Produces:* `data/processed/sensitivity_report.json`

9. **Report Generation**
 ```bash
 python code/09_generate_report.py
 ```
 *Produces:* `data/artifacts/final_report.md`

10. **Success Criteria Verification**
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Produces:* `data/artifacts/verification_status.json`, `data/artifacts/runtime_report.json`

## Notes

- Ensure `code/08_collinearity_check.py` is run after `code/03_compute_graph_metrics.py` as it depends on `data/processed/graph_metrics.csv`.
- All scripts respect the random seed `42` defined in `code/config.py`.
- Memory limits (7GB) are enforced during graph metric calculation.
