# Quickstart Guide for PROJ-256

This guide validates the entire pipeline execution.

This guide walks you through running the full data cleaning impact analysis pipeline.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Execution Steps

1. **Setup & Data Acquisition**
 ```bash
 python code/t011_ensure_data.py
 ```

2. **Baseline Analysis**
 ```bash
 python code/t012_run_baseline_analysis.py
 ```

3. **Clean Data & Re-analyze**
 ```bash
 python code/t022_save_cleaned_datasets.py
 python code/t023_reanalyze_cleaned_variants.py
 ```

4. **Comparison & Sensitivity**
 ```bash
 python code/t027_run_comparison.py
 python code/t030_dataset_size_sensitivity.py
 python code/t031_bootstrap_variance.py
 ```

5. **Permutation Null FPR (T032)**
 ```bash
 python code/t032_permutation_null_fpr.py
 ```

6. **Reporting & Visualization**
 ```bash
 python code/t034_generate_forest_plot.py
 python code/t035_generate_ci_heatmap.py
 python code/t036_pvalue_shift_reporting.py
 python code/t037_ci_width_reporting.py
 python code/t038_effect_size_reporting.py
 python code/t041_generate_final_report.py
 ```

## Validation
Run the validation script to ensure all artifacts are present:
```bash
python code/run_quickstart_validation.py
```

## Expected Artifacts
- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/null_fpr_metrics.json` (from T032)
- `figures/forest_plot.png`
- `figures/ci_heatmap.png`