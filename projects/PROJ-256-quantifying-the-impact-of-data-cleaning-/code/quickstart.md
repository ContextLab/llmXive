# Quickstart Guide

This guide shows how to run the full pipeline for the "Quantifying the Impact of Data Cleaning on Statistical Inference" project.

## Prerequisites

- Python 3.11+
- All dependencies installed (see `requirements.txt`)

## Installation

```bash
cd code
pip install -r requirements.txt
cd..
```

## Running the Pipeline

The pipeline consists of several sequential steps. Run them in order:

### Step 1: Ensure Data Exists

```bash
python code/t011_ensure_data.py
```

### Step 2: Run Baseline Analysis

```bash
python code/t012_run_baseline_analysis.py
```

### Step 3: Record Baseline Metrics

```bash
python code/t013_record_baseline_metrics.py
```

### Step 4: Apply Cleaning Strategies

```bash
python code/t022_save_cleaned_datasets.py
```

### Step 5: Re-analyze Cleaned Variants

```bash
python code/t023_reanalyze_cleaned_variants.py
```

### Step 6: Run Comparison Analysis

```bash
python code/t027_run_comparison.py
```

### Step 7: Dataset Size Sensitivity

```bash
python code/t030_dataset_size_sensitivity.py
```

### Step 8: Bootstrap Variance Estimation

```bash
python code/t031_bootstrap_variance.py
```

### Step 9: Permutation Null FPR

```bash
python code/t032_permutation_null_fpr.py
```

### Step 10: Outlier Threshold Sweep (T033)

```bash
python code/t033_outlier_threshold_sweep.py
```

### Step 11: Generate Forest Plot

```bash
python code/t034_generate_forest_plot.py
```

### Step 12: Generate CI Heatmap

```bash
python code/t035_generate_ci_heatmap.py
```

### Step 13: P-value Shift Reporting

```bash
python code/t036_pvalue_shift_reporting.py
```

### Step 14: CI Width Reporting

```bash
python code/t037_ci_width_reporting.py
```

### Step 15: Effect Size Reporting

```bash
python code/t038_effect_size_reporting.py
```

### Step 16: Log Excluded Datasets

```bash
python code/t039_log_excluded_datasets.py
```

### Step 17: Create Comparison Report

```bash
python code/t040_create_comparison_report.py
```

### Step 18: Generate Final Report

```bash
python code/t041_generate_final_report.py
```

## Verify Artifacts

After running the full pipeline, verify that all expected artifacts exist:

```bash
python code/run_quickstart_validation.py
```

## Expected Output Files

The pipeline produces the following artifacts in `data/processed/`:

- `baseline_metrics.json` - Baseline statistical metrics
- `cleaned_metrics.json` - Metrics after applying cleaning strategies
- `null_fpr_metrics.json` - False positive rate estimates from null datasets
- `outlier_threshold_sweep.json` - FPR and inconsistency rates across outlier thresholds
- `sensitivity_analysis.json` - Dataset size sensitivity analysis
- `bootstrap_variance.json` - Bootstrap variance estimates
- `comparison_report.json` - Comprehensive comparison report
- `forest_plot.png` - Visualization of p-value shifts
- `ci_heatmap.png` - Heatmap of CI width changes

## Troubleshooting

If you encounter errors:

1. Ensure all dependencies are installed
2. Check that data files exist in `data/raw/`
3. Verify that previous steps completed successfully
4. Check log output for specific error messages
