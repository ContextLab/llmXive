# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide provides the exact commands to run the full analysis pipeline end-to-end.
Ensure you are in the project root directory before executing these commands.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r code/requirements.txt`
- (Optional) FSL installed for motion correction (T018)

## Execution Order

Run the following commands in sequence. Each step produces artifacts required by the next.

1. **Data Gate**: Verify dataset availability
 ```bash
 python code/00_data_gate.py
 ```

2. **Download and Filter**: Download ds000246 and filter eligible subjects
 ```bash
 python code/01_download_and_filter.py
 ```
 *Outputs*: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

3. **Preprocess and Parcellate**: Motion correction, normalization, and atlas extraction
 ```bash
 python code/02_preprocess_and_parcellate.py
 ```
 *Outputs*: `data/processed/adjacency_matrices/`

4. **Compute Graph Metrics**: Calculate network topology metrics
 ```bash
 python code/03_compute_graph_metrics.py
 ```
 *Outputs*: `data/processed/graph_metrics.csv`

5. **Collinearity Check**: Standalone analysis of feature correlations (T044)
 ```bash
 python code/08_collinearity_check.py
 ```
 *Outputs*: `data/processed/collinearity_report.json`

6. **Train Model**: Nested CV with Random Forest
 ```bash
 python code/04_train_model.py
 ```
 *Outputs*: `data/processed/model.pkl`, `data/processed/cv_results.json`

7. **Evaluate Model**: Calculate performance metrics
 ```bash
 python code/05_evaluate_model.py
 ```
 *Outputs*: `data/processed/performance_report.json`

8. **Permutation Test**: Statistical significance validation
 ```bash
 python code/06_permutation_test.py
 ```
 *Outputs*: `data/processed/permutation_results.json`

9. **Sensitivity Analysis**: Threshold and label definition robustness
 ```bash
 python code/07_sensitivity_analysis.py
 ```
 *Outputs*: `data/processed/sensitivity_report.json`

10. **Generate Report**: Aggregate results
 ```bash
 python code/09_generate_report.py
 ```
 *Outputs*: `data/artifacts/final_report.md`

11. **Verify Success Criteria**: Check ROC-AUC, p-value, and runtime
 ```bash
 python code/10_verify_success_criteria.py
 ```
 *Outputs*: `VERIFICATION_STATUS`, `data/artifacts/runtime_report.json`

## Validation

Run the validation script to ensure all artifacts were produced correctly:
```bash
python code/validate_quickstart.py
```

## Notes

- **Runtime**: The full pipeline may take several hours depending on data size and hardware.
- **Memory**: Graph metric calculation (Step 4) is designed to stay under 7GB RAM.
- **Data**: This pipeline requires access to the OpenNeuro ds000246 dataset. If unavailable, the pipeline will exit with code 2.