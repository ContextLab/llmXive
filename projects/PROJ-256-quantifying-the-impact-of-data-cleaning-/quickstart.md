# Quickstart Guide: Quantifying the Impact of Data Cleaning

## Prerequisites
- Python 3.11+
- Installed dependencies (see `requirements.txt`)

## Installation
```bash
cd code
pip install -r requirements.txt
cd..
```

## Pipeline Execution
Run the full pipeline to download data, analyze, clean, and compare:

```bash
# 1. Ensure data exists (download if missing)
python code/t011_ensure_data.py

# 2. Run baseline analysis on raw data
python code/t012_run_baseline_analysis.py

# 3. Save cleaned datasets
python code/t022_save_cleaned_datasets.py

# 4. Re-analyze cleaned variants
python code/t023_reanalyze_cleaned_variants.py

# 5. Generate null FPR metrics
python code/t032_permutation_null_fpr.py

# 6. Run outlier threshold sweep (T033)
python code/t033_outlier_threshold_sweep.py

# 7. Generate reports and visualizations
python code/t036_pvalue_shift_reporting.py
python code/t037_ci_width_reporting.py
python code/t038_effect_size_reporting.py
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py

# 8. Generate final report
python code/t041_generate_final_report.py
```

## Expected Outputs
- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/null_fpr_metrics.json`
- `data/processed/threshold_sweep_metrics.json`
- `figures/*.png`
- `data/reports/final_report.md`

## Validation
```bash
python code/run_quickstart_validation.py
```
