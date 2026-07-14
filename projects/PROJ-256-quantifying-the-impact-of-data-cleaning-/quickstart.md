# Quickstart

This file drives the end‑to‑end pipeline execution used by the automated
verification harness. The commands are executed in order; each must
succeed and produce its declared artifacts.

```bash
# 1. Ensure raw data is present (downloads if necessary)
python code/t011_ensure_data.py

# 2. Run baseline analysis and record metrics
python code/t012_run_baseline_analysis.py
python code/t013_record_baseline_metrics.py

# 3. Apply cleaning strategies and re‑analyse
python code/t022_save_cleaned_datasets.py
python code/t023_reanalyze_cleaned_variants.py

# 4. Sensitivity analyses (including the new size‑bin analysis)
python code/t030_dataset_size_sensitivity.py
python code/t031_bootstrap_variance.py
python code/t032_permutation_null_fpr.py
python code/t033_outlier_threshold_sweep.py

# 5. Reporting / visualisations
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py
python code/t036_pvalue_shift_reporting.py
python code/t037_ci_width_reporting.py
python code/t038_effect_size_reporting.py
python code/t039_log_excluded_datasets.py
python code/t040_create_comparison_report.py
python code/t041_generate_final_report.py
```

After all commands have run, the final report can be inspected at
`output/final_report.txt`.