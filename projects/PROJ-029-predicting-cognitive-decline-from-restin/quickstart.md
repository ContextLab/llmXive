# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide outlines the execution order for the research pipeline.
All scripts must be run from the project root directory.

## Prerequisites

- Python 3.11+
- `pip install -r code/requirements.txt`
- Access to the internet (for initial dataset download)

## Execution Order

1. **Data Gate**: Verify dataset availability.
 ```bash
 python code/00_data_gate.py
 ```

2. **Download and Filter**: Download ds000246 and filter for eligible subjects.
 ```bash
 python code/01_download_and_filter.py
 ```
 *Outputs: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`*

3. **Preprocess and Parcellate**: Motion correction, normalization, and atlas application.
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Outputs: `data/processed/adjacency_matrices/`*

4. **Compute Graph Metrics**: Calculate network topology features.
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Outputs: `data/processed/graph_metrics.csv`*

5. **Collinearity Check**: Analyze feature correlations (T044).
 ```bash
 python code/08_collinearity_check.py
 ```
 *Outputs: `data/processed/collinearity_report.json`*

6. **Train Model**: Nested CV with Random Forest.
 ```bash
 python code/04_train_model.py
 ```
 *Outputs: `data/processed/model.pkl`, `data/processed/cv_results.json`*

7. **Evaluate Model**: Calculate performance metrics.
 ```bash
 python code/05_evaluate_model.py
 ```
 *Outputs: `data/processed/performance_report.json`*

8. **Permutation Test**: Validate statistical significance.
 ```bash
 python code/06_permutation_test.py
 ```
 *Outputs: `data/processed/permutation_results.json`*

9. **Sensitivity Analysis**: Threshold and label definition robustness.
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Outputs: `data/processed/sensitivity_report.json`*

10. **Generate Report**: Aggregate results into final report.
 ```bash
 python code/09_generate_report.py
 ```
 *Outputs: `data/artifacts/final_report.md`*

11. **Verify Success Criteria**: Check against research goals.
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Outputs: `data/artifacts/verification_status.json`, `data/artifacts/runtime_report.json`*

## Memory Profiling (Optional)

To profile memory usage for each step:
```bash
python code/15_run_ci_memory_profile.py
```

## Validation

To validate the entire quickstart sequence:
```bash
python code/validate_quickstart.py
```