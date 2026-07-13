# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide describes the end-to-end execution of the research pipeline.
Ensure you have installed dependencies via `pip install -r code/requirements.txt`
and that the dataset is available (see `code/00_data_gate.py`).

## Execution Order

Run the following commands in sequence from the project root:

1. **Data Ingestion & Filtering**
 ```bash
 python code/01_download_and_filter.py
 ```
 *Output*: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

2. **Preprocessing & Parcellation**
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Output*: `data/processed/adjacency_matrices/` (NIfTI matrices)

3. **Graph Metrics Calculation**
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Output*: `data/processed/graph_metrics.csv`

4. **Collinearity Analysis (Standalone Check)**
 ```bash
 python code/08_collinearity_check.py
 ```
 *Output*: `data/processed/collinearity_report.json`

5. **Model Training (Nested CV)**
 ```bash
 python code/04_train_model.py
 ```
 *Output*: `data/processed/model.pkl`, `data/processed/cv_results.json`

6. **Model Evaluation**
 ```bash
 python code/05_evaluate_model.py
 ```
 *Output*: `data/processed/performance_report.json`

7. **Permutation Test**
 ```bash
 python code/06_permutation_test.py
 ```
 *Output*: `data/processed/permutation_results.json`

8. **Sensitivity Analysis**
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Output*: `data/processed/sensitivity_report.json`

9. **Final Report Generation**
 ```bash
 python code/09_generate_report.py
 ```
 *Output*: `data/artifacts/final_report.md`

10. **Success Criteria Verification**
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Output*: `data/artifacts/verification_status.txt`, `data/artifacts/runtime_report.json`

## Notes

- Ensure `data/raw/` contains the downloaded BIDS dataset before running step 1.
- All scripts log to `logs/` and can be run independently if intermediate artifacts exist.
- Memory usage is monitored in step 3; ensure at least 7GB RAM is available.
- Step 6 (Permutation Test) requires a significant runtime (up to 2 hours); ensure the environment allows long-running processes.
