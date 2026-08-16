# Quickstart Guide: Predicting Individual Differences in Sensory Processing Speed

This guide describes how to run the full analysis pipeline end-to-end.
Ensure all prerequisites (Phase 1 & 2) are complete before running these steps.

## Prerequisites

- Python 3.8+
- Dependencies installed: `pip install -r code/requirements.txt`
- Data downloaded: Run `python code/01_download_data.py` first if not already done.

## Execution Order

The pipeline is designed to be run sequentially. Each step produces artifacts required by the next.

1. **Feasibility Check**: Verify data availability and alignment.
 ```bash
 python code/00_feasibility_check_join.py
 ```

2. **EEG Preprocessing**: Clean EEG data (Filter, ICA, Bad Channel Rejection).
 ```bash
 python code/02_preprocess_eeg.py
 ```

3. **Feature Extraction**: Compute PSD and band powers.
 ```bash
 python code/03_extract_features.py
 ```

4. **Behavioral Metrics**: Extract median RTs and exclusions.
 ```bash
 python code/04_extract_behavioral_metrics.py
 ```

5. **Relative Power**: Calculate relative band powers.
 ```bash
 python code/05_compute_relative_power.py
 ```

6. **Modeling**: Fit Linear/LASSO models and save results.
 ```bash
 python code/04_modeling.py
 ```

7. **Non-Linear Analysis**: Fit polynomial models and compare.
 ```bash
 python code/12_nonlinear_analysis.py
 ```

8. **Correlation & Bonferroni**: Run correlations and apply corrections.
 ```bash
 python code/08_correlation_analysis.py
 python code/09_apply_bonferroni.py
 ```

9. **Final Outputs (T025)**: Aggregate correlations and non-linear results.
 ```bash
 python code/13_generate_final_correlation_outputs.py
 ```

10. **Robustness & Sensitivity**: (Optional/Phase 3)
 ```bash
 python code/05_robustness_analysis.py
 python code/06_sensitivity_analysis.py
 ```

11. **Reporting**: Generate final markdown report.
 ```bash
 python code/07_generate_report.py
 ```

## Verification

After running the full pipeline, verify that the following files exist:
- `data/processed/features.csv`
- `data/processed/model_results.json`
- `data/processed/correlations.csv`
- `data/processed/non_linear_comparison.json`
- `data/processed/final_report.md`

Run the verification script:
```bash
python code/15_verify_success_criteria.py
```