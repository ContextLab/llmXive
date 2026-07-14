# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide walks you through the end-to-end execution of the research pipeline.
Ensure you have installed dependencies from `code/requirements.txt` and have network access
to download the dataset (if not cached).

## Prerequisites

- Python 3.11+
- FSL (for motion correction) - optional if using nilearn alternatives
- ~7GB RAM available

## Execution Steps

Run the following commands in order. Each script produces specific artifacts required by the next.

1. **Data Gate & Download**: Verify and download the dataset.
 ```bash
 python code/01_download_and_filter.py
 ```
 *Output*: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

2. **Preprocessing**: Generate connectivity matrices.
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Output*: `data/processed/connectivity_matrices/` (NIfTI or.npy files)

3. **Graph Metrics**: Compute topological features.
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Output*: `data/processed/graph_metrics.csv`

4. **Collinearity Check**: Standalone analysis of feature correlations.
 ```bash
 python code/08_collinearity_check.py
 ```
 *Output*: `data/processed/collinearity_report.json`

5. **Model Training**: Train the Random Forest with Nested CV.
 ```bash
 python code/04_train_model.py
 ```
 *Output*: `data/processed/model.pkl`, `data/processed/feature_selection_log.json`

6. **Evaluation**: Calculate performance metrics.
 ```bash
 python code/05_evaluate_model.py
 ```
 *Output*: `data/processed/performance_report.json`

7. **Permutation Test**: Assess statistical significance.
 ```bash
 python code/06_permutation_test.py
 ```
 *Output*: `data/processed/permutation_results.json`

8. **Sensitivity Analysis**: Test robustness of thresholds.
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Output*: `data/processed/sensitivity_report.json`

9. **Report Generation**: Aggregate results into a final report.
 ```bash
 python code/09_generate_report.py
 ```
 *Output*: `data/artifacts/final_report.md`

10. **Verification**: Check success criteria.
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Output*: `data/artifacts/verification_status.txt`, `data/artifacts/runtime_report.json`

## Notes

- If the dataset download fails due to network issues, ensure `api.openneuro.org` is reachable or use a local cache if configured.
- The `code/08_collinearity_check.py` script is now explicitly included in the run-book to satisfy the dependency contract with the run-book documentation.