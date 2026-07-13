# Quickstart Guide

This guide outlines the steps to run the full pipeline for the project.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`

## Execution Steps

Run the following commands in order to execute the full research pipeline:

1. **Download Datasets**
 ```bash
 python code/t011_download_datasets.py
 ```

2. **Run Baseline Analysis (T012)**
 ```bash
 python code/t012_run_baseline_analysis.py
 ```

3. **Record Baseline Metrics (T013)**
 ```bash
 python code/t013_record_baseline_metrics.py
 ```

4. **Apply Cleaning Strategies (T022)**
 ```bash
 python code/t022_save_cleaned_datasets.py
 ```

5. **Re-analyze Cleaned Variants (T023)**
 ```bash
 python code/t023_reanalyze_cleaned_variants.py
 ```

6. **Run Sensitivity Analysis & Reporting (T030-T041)**
 ```bash
 python code/t030_dataset_size_sensitivity.py
 python code/t031_bootstrap_variance.py
 python code/t032_permutation_null_fpr.py
 python code/t033_outlier_threshold_sweep.py
 python code/t034_generate_forest_plot.py
 python code/t035_generate_ci_heatmap.py
 python code/t036_pvalue_shift_reporting.py
 python code/t037_ci_width_reporting.py
 python code/t038_effect_size_reporting.py
 python code/t039_log_excluded_datasets.py
 python code/t040_create_comparison_report.py
 python code/t041_generate_final_report.py
 ```

7. **Verify Artifacts**
 ```bash
 python code/t048_verify_checksums_and_state.py
 ```

## Expected Outputs

- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/null_fpr_metrics.json`
- `figures/*.png`
- `output/final_report.txt`