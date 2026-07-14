# Quickstart Guide for Quantifying the Impact of Data Cleaning on Statistical Inference

## Prerequisites
- Python 3.11+
- Project dependencies installed (see `requirements.txt`)

## Setup
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure data is available (run T011 if needed):
 ```bash
 python code/t011_ensure_data.py
 ```

## Pipeline Execution
Run the following commands in order to execute the full pipeline and generate all artifacts:

1. **Baseline Analysis**:
 ```bash
 python code/t012_run_baseline_analysis.py
 ```

2. **Cleaning & Re-analysis**:
 ```bash
 python code/t022_save_cleaned_datasets.py
 python code/t023_reanalyze_cleaned_variants.py
 ```

3. **Comparison & Reporting**:
 ```bash
 python code/t027_run_comparison.py
 python code/t036_pvalue_shift_reporting.py
 python code/t037_ci_width_reporting.py
 python code/t038_effect_size_reporting.py
 ```

4. **Sensitivity Analysis**:
 ```bash
 python code/t030_dataset_size_sensitivity.py
 python code/t031_bootstrap_variance.py
 ```

5. **Null Hypothesis & Threshold Sweep**:
 ```bash
 python code/t032_permutation_null_fpr.py
 python code/t033_outlier_threshold_sweep.py
 ```

6. **Visualizations**:
 ```bash
 python code/t034_generate_forest_plot.py
 python code/t035_generate_ci_heatmap.py
 ```

7. **Final Report**:
 ```bash
 python code/t041_generate_final_report.py
 ```

## Verification
Validate all artifacts:
```bash
python code/run_quickstart_validation.py
```

## Output Artifacts
- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/null_fpr_metrics.json`
- `data/processed/outlier_threshold_sweep.json`
- `figures/` (PNG plots)
- `data/processed/final_report.md`