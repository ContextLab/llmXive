# Quickstart Guide: Quantifying the Impact of Data Cleaning on Statistical Inference

## Prerequisites
- Python 3.11+
- Virtual environment activated

## Installation
```bash
pip install -r requirements.txt
```

## Pipeline Execution
Run the following commands in order to execute the full pipeline:

1. **Ensure Data Availability**
 ```bash
 python code/t011_ensure_data.py
 ```

2. **Run Baseline Analysis**
 ```bash
 python code/t012_run_baseline_analysis.py
 ```

3. **Record Baseline Metrics**
 ```bash
 python code/t013_record_baseline_metrics.py
 ```

4. **Save Cleaned Datasets**
 ```bash
 python code/t022_save_cleaned_datasets.py
 ```

5. **Re-analyze Cleaned Variants**
 ```bash
 python code/t023_reanalyze_cleaned_variants.py
 ```

6. **Generate Permutation Null FPR**
 ```bash
 python code/t032_permutation_null_fpr.py
 ```

7. **Run Outlier Threshold Sweep**
 ```bash
 python code/t033_outlier_threshold_sweep.py
 ```

8. **Run Comparison Analysis**
 ```bash
 python code/t027_run_comparison.py
 ```

9. **Run Dataset Size Sensitivity**
 ```bash
 python code/t030_dataset_size_sensitivity.py
 ```

10. **Run Bootstrap Variance**
 ```bash
 python code/t031_bootstrap_variance.py
 ```

11. **Generate Forest Plot**
 ```bash
 python code/t034_generate_forest_plot.py
 ```

12. **Generate CI Heatmap**
 ```bash
 python code/t035_generate_ci_heatmap.py
 ```

13. **P-value Shift Reporting**
 ```bash
 python code/t036_pvalue_shift_reporting.py
 ```

14. **CI Width Reporting**
 ```bash
 python code/t037_ci_width_reporting.py
 ```

15. **Effect Size Reporting**
 ```bash
 python code/t038_effect_size_reporting.py
 ```

16. **Log Excluded Datasets**
 ```bash
 python code/t039_log_excluded_datasets.py
 ```

17. **Create Comparison Report (T040)**
 ```bash
 python code/t040_create_comparison_report.py
 ```

18. **Generate Final Report**
 ```bash
 python code/t041_generate_final_report.py
 ```

19. **Verify Checksums and State**
 ```bash
 python code/t048_verify_checksums_and_state.py
 ```

## Output Artifacts
The pipeline produces the following artifacts in `data/processed/`:
- `baseline_metrics.json`
- `cleaned_metrics.json`
- `null_fpr_metrics.json`
- `comparison_report.json`
- `final_report.json`
- `forest_plot.png`
- `ci_heatmap.png`

## Validation
To validate the pipeline execution:
```bash
python code/run_quickstart_validation.py
```