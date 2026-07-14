# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide outlines the end-to-end execution of the research pipeline for Project
**PROJ-029**. All scripts must be run from the project root directory.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r code/requirements.txt`
- Network access to download the OpenNeuro dataset `ds000246`

## Execution Order

Run the following commands sequentially. Each step produces artifacts required by subsequent steps.

1. **Data Ingestion and Filtering**
 ```bash
 python code/01_download_and_filter.py
 ```
 *Outputs:* `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`, `data/artifacts/data_gate_status.json`

2. **Preprocessing and Parcellation**
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Outputs:* `data/processed/connectivity_matrices/` (NIfTI files)

3. **Graph Metric Calculation**
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Outputs:* `data/processed/graph_metrics.csv`

4. **Model Training (Nested CV)**
 ```bash
 python code/04_train_model.py
 ```
 *Outputs:* `data/processed/model.pkl`, `data/processed/cv_results.json`, `data/processed/model_params.json`

5. **Model Evaluation**
 ```bash
 python code/05_evaluate_model.py
 ```
 *Outputs:* `data/processed/performance_report.json`

6. **Permutation Test**
 ```bash
 python code/06_permutation_test.py
 ```
 *Outputs:* `data/processed/permutation_results.json`

7. **Sensitivity Analysis**
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Outputs:* `data/processed/sensitivity_report.json`

8. **External Outcome Check**
 ```bash
 python code/11_external_outcome_check.py
 ```
 *Outputs:* `data/artifacts/limitations.txt`

9. **Report Generation**
 ```bash
 python code/09_generate_report.py
 ```
 *Outputs:* `data/artifacts/final_report.md`

10. **Success Criteria Verification**
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Outputs:* `data/artifacts/verification_status.json`, `data/artifacts/runtime_report.json`

## Notes

- The standalone script `code/08_collinearity_check.py` has been removed. Collinearity handling is now integrated directly into the training pipeline (`code/04_train_model.py`) as per the revised specification.
- Ensure sufficient disk space for the downloaded dataset and intermediate connectivity matrices.
- The pipeline assumes a 2-core runner with 7GB RAM limit; memory profiling is handled internally where applicable.

## Validation

To validate the entire pipeline:
```bash
python code/validate_quickstart.py
```
This script runs the sequence above and verifies the existence of all declared output artifacts.