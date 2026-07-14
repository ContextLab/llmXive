# Quickstart Guide for PROJ-256

This guide walks you through the automated science pipeline for quantifying the impact of data cleaning.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Execution Steps

Run the following commands in order to execute the full pipeline:

1. **Ensure Data**: Download and prepare raw datasets.
 ```bash
 python code/t011_ensure_data.py
 ```

2. **Run Baseline Analysis**: Analyze raw data to establish reference metrics.
 ```bash
 python code/t012_run_baseline_analysis.py
 ```

3. **Record Baseline Metrics**: Save baseline metrics to JSON.
 ```bash
 python code/t013_record_baseline_metrics.py
 ```

4. **Apply Cleaning Strategies**: Clean data and save variants.
 ```bash
 python code/t022_save_cleaned_datasets.py
 ```

5. **Re-analyze Cleaned Variants**: Analyze cleaned data.
 ```bash
 python code/t023_reanalyze_cleaned_variants.py
 ```

6. **Record Cleaned Metrics**: Save cleaned metrics.
 ```bash
 python code/t027_run_comparison.py
 ```

7. **Run Comparison & Sensitivity**: Compare baseline vs cleaned.
 ```bash
 python code/t027_run_comparison.py
 ```

8. **Bootstrap Variance**: Estimate variance of metric shifts.
 ```bash
 python code/t031_bootstrap_variance.py
 ```

9. **Permutation Null FPR**: Estimate false positive rate via permutation.
 ```bash
 python code/t032_permutation_null_fpr.py
 ```

10. **Generate Visualizations**: Create forest plots and heatmaps.
 ```bash
 python code/t034_generate_forest_plot.py
 python code/t035_generate_ci_heatmap.py
 ```

11. **Generate Reports**: Create per-dataset and final reports.
 ```bash
 python code/t036_pvalue_shift_reporting.py
 python code/t037_ci_width_reporting.py
 python code/t038_effect_size_reporting.py
 python code/t041_generate_final_report.py
 ```

12. **Verify Artifacts**: Check checksums and state.
 ```bash
 python code/t048_verify_checksums_and_state.py
 ```

## Expected Outputs

- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/null_fpr_metrics.json`
- `figures/` (plots)
- `data/reports/` (final reports)