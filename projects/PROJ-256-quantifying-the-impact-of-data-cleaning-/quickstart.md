# llmXive Research Pipeline - Quickstart

This document describes how to run the full research pipeline for the project
"Quantifying the Impact of Data Cleaning on Statistical Inference".

## Prerequisites

- Python 3.11+
- Required packages (install via `pip install -r requirements.txt`)

## Quickstart Commands

Run the following commands in order to execute the full pipeline:

```bash
# 1. Ensure data exists (download if needed)
python code/t011_ensure_data.py

# 2. Run baseline analysis on raw data
python code/t012_run_baseline_analysis.py

# 3. Record baseline metrics
python code/t013_record_baseline_metrics.py

# 4. Apply cleaning strategies and save cleaned datasets
python code/t022_save_cleaned_datasets.py

# 5. Re-analyze cleaned variants
python code/t023_reanalyze_cleaned_variants.py

# 6. Run comparison analysis
python code/t027_run_comparison.py

# 7. Run dataset size sensitivity analysis
python code/t030_dataset_size_sensitivity.py

# 8. Run bootstrap variance estimation
python code/t031_bootstrap_variance.py

# 9. Run permutation null FPR estimation
python code/t032_permutation_null_fpr.py

# 10. Run outlier threshold sweep (T033)
python code/t033_outlier_threshold_sweep.py

# 11. Generate forest plot
python code/t034_generate_forest_plot.py

# 12. Generate CI width heatmap
python code/t035_generate_ci_heatmap.py

# 13. Generate p-value shift report
python code/t036_pvalue_shift_reporting.py

# 14. Generate CI width report
python code/t037_ci_width_reporting.py

# 15. Generate effect size report
python code/t038_effect_size_reporting.py

# 16. Log excluded datasets
python code/t039_log_excluded_datasets.py

# 17. Create comparison report
python code/t040_create_comparison_report.py

# 18. Generate final report
python code/t041_generate_final_report.py

# 19. Verify checksums and update state
python code/t048_verify_checksums_and_state.py
```

## Expected Outputs

After successful execution, the following artifacts should exist:

- `data/processed/baseline_metrics.json` - Baseline statistical metrics
- `data/processed/cleaned_metrics.json` - Metrics after cleaning
- `data/processed/null_fpr_metrics.json` - Null distribution FPR metrics
- `data/processed/threshold_sweep_results.json` - Outlier threshold sweep results (T033)
- `figures/forest_plot.png` - Forest plot visualization
- `figures/ci_heatmap.png` - CI width heatmap visualization
- `data/reports/comparison_report.json` - Detailed comparison report
- `data/reports/final_report.md` - Final research report

## Troubleshooting

If you encounter errors:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check that data files exist in `data/raw/`
3. Verify environment variables in `.env` if using custom paths
4. Review logs for specific error messages