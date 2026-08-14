# Quickstart Guide for PROJ-149

This guide explains how to run the pipeline end-to-end.

## Prerequisites

- Python 3.9+
- Installed dependencies: `pip install -r code/requirements.txt`

## Execution Order

The pipeline must be executed in the following order to ensure data availability:

1. **Download Data**: Fetch PhysioNet EEG Motor Movement/Imagery dataset.
2. **Feasibility Check**: Verify data compatibility.
3. **Preprocess EEG**: Apply filters and ICA.
4. **Extract Features**: Compute PSD and behavioral metrics.
5. **Modeling**: Fit predictive models.
6. **Reporting**: Generate final report.

## Run Book

Execute the following commands in sequence:

```bash
# 1. Setup (if not done)
python code/setup_project.py

# 2. Download Data (T007)
python code/01_download_data.py

# 3. Feasibility Check (T008a)
python code/00_feasibility_check_join.py

# 4. Preprocess EEG (T010a, T010b)
python code/02_preprocess_eeg.py

# 5. Extract EEG Features (T012)
python code/03_extract_features.py

# 6. Extract Behavioral Metrics (T013) - NEWLY ADDED
python code/04_extract_behavioral_metrics.py

# 7. Compute Relative Power (T015)
python code/05_compute_relative_power.py

# 8. Modeling (T017, T018, T019)
python code/04_modeling.py

# 9. Correlation Analysis (T020, T021)
python code/08_correlation_analysis.py
python code/09_apply_bonferroni.py

# 10. Non-linear Analysis (T024)
python code/12_nonlinear_analysis.py

# 11. Robustness Analysis (T026, T027)
python code/05_robustness_analysis.py

# 12. Sensitivity Analysis (T028, T029)
python code/06_sensitivity_analysis.py
python code/07_generate_sensitivity_plot.py

# 13. Generate Final Report (T031)
python code/07_generate_report.py

# 14. Verify Success Criteria (T032)
python code/15_verify_success_criteria.py
```

## Expected Outputs

After successful execution, the following files should be present:

- `data/interim/behavioral_metrics.csv`
- `data/interim/behavioral_exclusion_log.csv`
- `data/interim/eeg_psd.csv`
- `data/processed/features.csv`
- `data/processed/model_results.json`
- `data/processed/final_report.md`

## Troubleshooting

- **Missing Data**: Ensure `code/01_download_data.py` completes successfully.
- **Import Errors**: Verify all dependencies are installed.
- **Path Errors**: Check `code/config.py` for correct path definitions.