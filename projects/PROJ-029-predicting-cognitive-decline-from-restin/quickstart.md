# Quick Start Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide describes the execution order for the research pipeline.
All commands must be run from the project root.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r code/requirements.txt`
- OpenNeuro `ds000246` dataset access (handled by `01_download_and_filter.py`)

## Execution Order

Run the following scripts in sequence. Each script produces artifacts consumed by the next.

1. **Data Ingestion & Filtering**
 ```bash
 python code/01_download_and_filter.py
 ```
 *Outputs*: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

2. **Preprocessing & Parcellation**
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Outputs*: `data/processed/connectivity_matrices/` (NIfTI files)

3. **Graph Metric Computation**
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Outputs*: `data/processed/graph_metrics.csv`

4. **Model Training (Nested CV)**
 ```bash
 python code/04_train_model.py
 ```
 *Outputs*: `data/processed/model.pkl`, `data/processed/cv_results.json`, `data/processed/model_params.json`

5. **Model Evaluation**
 ```bash
 python code/05_evaluate_model.py
 ```
 *Outputs*: `data/processed/performance_report.json`

6. **Permutation Test**
 ```bash
 python code/06_permutation_test.py
 ```
 *Outputs*: `data/processed/permutation_results.json`

7. **Sensitivity Analysis**
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Outputs*: `data/processed/sensitivity_report.json`

8. **External Outcome Check**
 ```bash
 python code/11_external_outcome_check.py
 ```
 *Outputs*: `data/artifacts/limitations.txt`

9. **Report Generation**
 ```bash
 python code/09_generate_report.py
 ```
 *Outputs*: `data/artifacts/final_report.md`

10. **Success Criteria Verification**
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Outputs*: `data/artifacts/verification_status.json`, `data/artifacts/runtime_report.json`

## Notes

- The standalone `code/08_collinearity_check.py` has been deprecated. Collinearity handling is now integrated directly into `code/04_train_model.py` as per the updated specification.
- Ensure `data/raw/` and `data/processed/` directories exist before running.
- Random seeds are fixed at 42 for reproducibility.