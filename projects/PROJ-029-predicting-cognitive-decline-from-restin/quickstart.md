# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide walks you through running the full pipeline to reproduce the analysis.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r code/requirements.txt`
- Access to the dataset (ds000246 from OpenNeuro or equivalent)

## Execution Order

Run the following commands in order from the project root:

1. **Data Ingestion & Filtering**
 ```bash
 python code/01_download_and_filter.py
 ```
 *Produces: `data/processed/eligible_subjects.csv`*

2. **Preprocessing & Parcellation**
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Produces: Connectivity matrices in `data/processed/`*

3. **Graph Metrics Computation**
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Produces: `data/processed/graph_metrics.csv`*

4. **Collinearity Check**
 ```bash
 python code/08_collinearity_check.py
 ```
 *Produces: `data/processed/collinearity_report.json`*

5. **Model Training**
 ```bash
 python code/04_train_model.py
 ```
 *Produces: `data/processed/model.pkl`*

6. **Model Evaluation**
 ```bash
 python code/05_evaluate_model.py
 ```
 *Produces: `data/processed/performance_report.json`*

7. **Permutation Test**
 ```bash
 python code/06_permutation_test.py
 ```
 *Produces: `data/processed/permutation_results.json`*

8. **Sensitivity Analysis**
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Produces: `data/processed/sensitivity_report.json`*

9. **Report Generation**
 ```bash
 python code/09_generate_report.py
 ```
 *Produces: `data/artifacts/final_report.md`*

10. **Success Verification**
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Produces: `data/artifacts/verification_status.json`*

## Validation

To validate the entire run-book:
```bash
python code/validate_quickstart.py
```

## Notes

- Ensure `data/raw/` is writable if downloading data.
- The pipeline assumes a 7GB RAM limit; use `code/12_memory_profiler.py` to monitor.
- Random seeds are fixed at 42 for reproducibility.