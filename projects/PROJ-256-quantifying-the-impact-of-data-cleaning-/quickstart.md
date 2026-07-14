# Quickstart Guide for Quantifying the Impact of Data Cleaning

This guide outlines the steps to run the full analysis pipeline.

## Prerequisites

- Python 3.11+
- All dependencies installed via `pip install -r requirements.txt`

## Execution Steps

1. **Ensure Data Exists**:
 ```bash
 python code/t011_ensure_data.py
 ```

2. **Run Baseline Analysis**:
 ```bash
 python code/t012_run_baseline_analysis.py
 ```
 This generates `data/processed/baseline_metrics.json`.

3. **Apply Cleaning Strategies**:
 ```bash
 python code/t022_save_cleaned_datasets.py
 ```

4. **Re-analyze Cleaned Variants**:
 ```bash
 python code/t023_reanalyze_cleaned_variants.py
 ```

5. **Run Comparison and Sensitivity Analysis**:
 ```bash
 python code/t027_run_comparison.py
 python code/t030_dataset_size_sensitivity.py
 python code/t031_bootstrap_variance.py
 ```

6. **Permutation Null FPR Estimation (T032)**:
 ```bash
 python code/t032_permutation_null_fpr.py
 ```
 This generates `data/processed/null_fpr_metrics.json`.

7. **Generate Visualizations and Reports**:
 ```bash
 python code/t034_generate_forest_plot.py
 python code/t035_generate_ci_heatmap.py
 python code/t036_pvalue_shift_reporting.py
 python code/t037_ci_width_reporting.py
 python code/t038_effect_size_reporting.py
 python code/t041_generate_final_report.py
 ```

8. **Verify Artifacts**:
 ```bash
 python code/t048_verify_checksums_and_state.py
 ```

## Expected Outputs

- `data/processed/baseline_metrics.json`: Baseline statistical metrics.
- `data/processed/cleaned_metrics.json`: Metrics after cleaning.
- `data/processed/null_fpr_metrics.json`: False Positive Rate estimates from permutation testing.
- `figures/`: Generated plots (forest plot, heatmap).
- `output/final_report.md`: Final analysis report.

## Troubleshooting

- If `data/raw` is empty, run `python code/t011_ensure_data.py` first.
- Ensure `outcome_col` and `group_col` in `data/processed/*.csv` match the config or defaults.
- Check logs for specific errors in `logs/`.