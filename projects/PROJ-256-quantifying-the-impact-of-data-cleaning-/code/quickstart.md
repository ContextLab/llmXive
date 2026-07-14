# Quickstart Guide

This guide outlines the steps to run the full analysis pipeline.

## Prerequisites

- Python 3.11+
- Virtual environment activated

## Setup

```bash
pip install -r requirements.txt
```

## Run the Pipeline

Execute the following scripts in order:

1. **Ensure Data Exists** (Download datasets if missing)
 ```bash
 python code/t011_ensure_data.py
 ```

2. **Run Baseline Analysis** (Analyze raw data)
 ```bash
 python code/t012_run_baseline_analysis.py
 ```

3. **Save Cleaned Datasets** (Apply cleaning strategies)
 ```bash
 python code/t022_save_cleaned_datasets.py
 ```

4. **Reanalyze Cleaned Variants** (Analyze cleaned data)
 ```bash
 python code/t023_reanalyze_cleaned_variants.py
 ```

5. **Run Comparison** (Compare baseline vs cleaned)
 ```bash
 python code/t027_run_comparison.py
 ```

6. **Bootstrap Variance** (Estimate variance of shifts)
 ```bash
 python code/t031_bootstrap_variance.py
 ```

7. **Permutation Null FPR** (Estimate False Positive Rate)
 ```bash
 python code/t032_permutation_null_fpr.py
 ```

8. **Outlier Threshold Sweep** (Sweep k values)
 ```bash
 python code/t033_outlier_threshold_sweep.py
 ```

9. **Generate Visualizations**
 ```bash
 python code/t034_generate_forest_plot.py
 python code/t035_generate_ci_heatmap.py
 ```

10. **Generate Final Report**
 ```bash
 python code/t041_generate_final_report.py
 ```

## Output Artifacts

All processed data and reports will be saved in `data/processed/`:
- `baseline_metrics.json`
- `cleaned_metrics.json`
- `null_fpr_metrics.json`
- `comparison_report.json`
- `forest_plot.png`
- `ci_heatmap.png`
