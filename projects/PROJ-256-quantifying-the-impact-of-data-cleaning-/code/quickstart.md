# Quickstart Guide

This guide outlines the steps to run the full pipeline for the project "Quantifying the Impact of Data Cleaning on Statistical Inference".

## Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

## Setup

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Pipeline Execution

The pipeline is executed via a series of scripts. Run them in order:

1. **Ensure Data Exists** (Downloads datasets if missing):
 ```bash
 python code/t011_ensure_data.py
 ```

2. **Run Baseline Analysis** (Computes metrics on raw data):
 ```bash
 python code/t012_run_baseline_analysis.py
 ```

3. **Record Baseline Metrics** (Saves baseline to JSON):
 ```bash
 python code/t013_record_baseline_metrics.py
 ```

4. **Save Cleaned Datasets** (Applies cleaning strategies):
 ```bash
 python code/t022_save_cleaned_datasets.py
 ```

5. **Reanalyze Cleaned Variants** (Computes metrics on cleaned data):
 ```bash
 python code/t023_reanalyze_cleaned_variants.py
 ```

6. **Run Comparison** (Compares baseline vs cleaned):
 ```bash
 python code/t027_run_comparison.py
 ```

7. **Dataset Size Sensitivity**:
 ```bash
 python code/t030_dataset_size_sensitivity.py
 ```

8. **Bootstrap Variance Estimation**:
 ```bash
 python code/t031_bootstrap_variance.py
 ```

9. **Permutation Null FPR**:
 ```bash
 python code/t032_permutation_null_fpr.py
 ```

10. **Outlier Threshold Sweep** (T033):
 ```bash
 python code/t033_outlier_threshold_sweep.py
 ```

11. **Generate Forest Plot**:
 ```bash
 python code/t034_generate_forest_plot.py
 ```

12. **Generate CI Heatmap**:
 ```bash
 python code/t035_generate_ci_heatmap.py
 ```

13. **Per-Dataset Reporting**:
 ```bash
 python code/t036_pvalue_shift_reporting.py
 python code/t037_ci_width_reporting.py
 python code/t038_effect_size_reporting.py
 ```

14. **Log Excluded Datasets**:
 ```bash
 python code/t039_log_excluded_datasets.py
 ```

15. **Create Comparison Report**:
 ```bash
 python code/t040_create_comparison_report.py
 ```

16. **Generate Final Report**:
 ```bash
 python code/t041_generate_final_report.py
 ```

17. **Verify Checksums and State**:
 ```bash
 python code/t048_verify_checksums_and_state.py
 ```

## Output Artifacts

All processed data and reports are saved in `data/processed/`:
- `baseline_metrics.json`
- `cleaned_metrics.json`
- `null_fpr_metrics.json`
- `threshold_sweep_metrics.json`
- `comparison_report.json`
- `final_report.txt`
- `forest_plot.png`
- `ci_heatmap.png`

## Troubleshooting

- If data download fails, check your internet connection and the dataset URLs in `code/t011_ensure_data.py`.
- If analysis fails, ensure all required Python packages are installed.
- For logging issues, check the `LOG_LEVEL` environment variable or the `setup_logging` function in `code/utils.py`.