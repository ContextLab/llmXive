# Quick Start Guide

This guide provides the commands to run the full analysis pipeline for predicting cognitive decline from resting-state fMRI network topology.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r code/requirements.txt`
- Access to the OpenNeuro ds000246 dataset (handled automatically by the download script)

## Execution Order

Run the following commands in sequence. Each command produces artifacts required by the next.

1. **Data Ingestion and Filtering**
 ```bash
 python code/01_download_and_filter.py
 ```
 *Produces*: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

2. **Preprocessing and Parcellation**
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Produces*: Connectivity matrices in `data/processed/connectivity_matrices/`

3. **Graph Metric Calculation**
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Produces*: `data/processed/graph_metrics.csv`

4. **Model Training**
 ```bash
 python code/04_train_model.py
 ```
 *Produces*: `data/processed/model.pkl`, `data/processed/cv_results.json`, `data/processed/model_params.json`

5. **Model Evaluation**
 ```bash
 python code/05_evaluate_model.py
 ```
 *Produces*: `data/processed/performance_report.json`

6. **Permutation Test**
 ```bash
 python code/06_permutation_test.py
 ```
 *Produces*: `data/processed/permutation_results.json`

7. **Sensitivity Analysis**
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Produces*: `data/processed/sensitivity_report.json`

8. **External Outcome Check**
 ```bash
 python code/11_external_outcome_check.py
 ```
 *Produces*: `data/artifacts/limitations.txt`

9. **Report Generation**
 ```bash
 python code/09_generate_report.py
 ```
 *Produces*: `data/artifacts/final_report.md`

10. **Success Criteria Verification**
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Produces*: `data/artifacts/verification_status.txt`, `data/artifacts/runtime_report.json`

## Validation

To verify the entire pipeline and artifacts:
```bash
python code/validate_quickstart.py
```

## Notes

- The standalone collinearity check script (`code/08_collinearity_check.py`) has been removed. Collinearity handling is now integrated directly into the model training step (`code/04_train_model.py`) as per the updated plan.
- Ensure you have sufficient disk space for the downloaded dataset and intermediate connectivity matrices.
- The pipeline respects the 7GB RAM limit by processing subjects sequentially where applicable.