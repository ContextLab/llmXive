# Quickstart Guide for PROJ-256-quantifying-the-impact-of-data-cleaning-

This guide walks you through the execution of the data cleaning impact analysis pipeline.

## Prerequisites

- Python 3.11+
- Virtual environment activated
- Dependencies installed (`pip install -r requirements.txt`)

## Execution Steps

Run the following commands in order to execute the full pipeline:

1. **Ensure Data Availability**
 ```bash
 python code/t011_ensure_data.py
 ```

2. **Run Baseline Analysis**
 ```bash
 python code/t012_run_baseline_analysis.py
 ```

3. **Save Cleaned Datasets**
 ```bash
 python code/t022_save_cleaned_datasets.py
 ```

4. **Re-analyze Cleaned Variants**
 ```bash
 python code/t023_reanalyze_cleaned_variants.py
 ```

5. **Run Comparison Analysis**
 ```bash
 python code/t027_run_comparison.py
 ```

6. **Generate Sensitivity Analysis**
 ```bash
 python code/t030_dataset_size_sensitivity.py
 ```

7. **Run Bootstrap Variance Estimation**
 ```bash
 python code/t031_bootstrap_variance.py
 ```

8. **Generate Permutation Null FPR**
 ```bash
 python code/t032_permutation_null_fpr.py
 ```

9. **Run Outlier Threshold Sweep**
 ```bash
 python code/t033_outlier_threshold_sweep.py
 ```

10. **Generate Visualizations**
 ```bash
 python code/t034_generate_forest_plot.py
 python code/t035_generate_ci_heatmap.py
 ```

11. **Generate Reporting Metrics**
 ```bash
 python code/t036_pvalue_shift_reporting.py
 python code/t037_ci_width_reporting.py
 python code/t038_effect_size_reporting.py
 python code/t039_log_excluded_datasets.py
 ```

12. **Create Comparison Report (T040)**
 ```bash
 python code/t040_create_comparison_report.py
 ```

13. **Generate Final Report**
 ```bash
 python code/t041_generate_final_report.py
 ```

## Output Artifacts

After successful execution, the following artifacts will be available in `data/processed/`:
- `baseline_metrics.json`
- `cleaned_metrics.json`
- `comparison_report.json`
- `null_fpr_metrics.json`
- `sensitivity_analysis.json`
- Visualizations (PNGs) in `data/processed/figures/`

## Troubleshooting

- If you encounter "No such file or directory" errors, ensure the virtual environment is activated and you are running from the project root.
- If data files are missing, run `python code/t011_ensure_data.py` first.
- Check `logs/` directory for detailed execution logs.
