# Quickstart Guide: Predicting Individual Differences in Sensory Processing Speed

This guide provides the commands to run the full pipeline end-to-end.

## Prerequisites

```bash
# Install dependencies
pip install -r code/requirements.txt
```

## Full Pipeline Execution

Run all steps in sequence:

```bash
# 1. Download data
python code/01_download_data.py

# 2. Feasibility check
python code/00_feasibility_check_join.py

# 3. Preprocess EEG
python code/02_preprocess_eeg.py

# 4. Extract features (T012)
python code/03_extract_features.py

# 5. Extract behavioral metrics
python code/04_extract_behavioral_metrics.py

# 6. Compute relative power (T015)
python code/05_compute_relative_power.py

# 7. Modeling (T017)
python code/04_modeling.py

# 8. LASSO (T018)
python code/04_modeling_lasso.py

# 9. Correlation analysis (T020)
python code/08_correlation_analysis.py

# 10. Bonferroni correction (T021)
python code/09_apply_bonferroni.py

# 11. Permutation test (T022)
python code/10_perform_permutation_test.py

# 12. Non-linear analysis (T024)
python code/12_nonlinear_analysis.py

# 13. Generate final outputs (T025)
python code/13_generate_final_correlation_outputs.py

# 14. Robustness analysis (T026)
python code/05_robustness_analysis.py

# 15. Sensitivity analysis (T028)
python code/06_sensitivity_analysis.py

# 16. Generate report (T031)
python code/07_generate_report.py

# 17. Verify success criteria (T032)
python code/15_verify_success_criteria.py
```

## Output Files

The pipeline produces the following key outputs:

- `data/interim/eeg_psd.csv` - Raw band power features (T012)
- `data/interim/behavioral_metrics.csv` - Median RT and trial counts
- `data/processed/features.csv` - Final feature matrix with relative power
- `data/processed/model_results.json` - Model performance metrics
- `data/processed/correlations.csv` - Correlation results with Bonferroni flags
- `data/processed/final_report.md` - Comprehensive analysis report