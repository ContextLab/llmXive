# llmXive Research Pipeline - Quickstart

This document describes how to run the full research pipeline for the "Quantifying the Impact of Data Cleaning on Statistical Inference" project.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`

## Execution Steps

The pipeline is executed by running a sequence of scripts. The main entry point is `code/main.py`, which orchestrates the steps.

### 1. Ensure Data is Available

```bash
python code/t011_ensure_data.py
```

### 2. Run Baseline Analysis

```bash
python code/t012_run_baseline_analysis.py
```

### 3. Record Baseline Metrics

```bash
python code/t013_record_baseline_metrics.py
```

### 4. Apply Cleaning Strategies and Re-analyze

```bash
python code/t022_save_cleaned_datasets.py
python code/t023_reanalyze_cleaned_variants.py
```

### 5. Generate Null Datasets and FPR Metrics

```bash
python code/t032_permutation_null_fpr.py
```

### 6. Run Outlier Threshold Sweep (T033)

```bash
python code/t033_outlier_threshold_sweep.py
```

### 7. Run Sensitivity and Reporting Analyses

```bash
python code/t027_run_comparison.py
python code/t030_dataset_size_sensitivity.py
python code/t031_bootstrap_variance.py
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py
python code/t036_pvalue_shift_reporting.py
python code/t037_ci_width_reporting.py
python code/t038_effect_size_reporting.py
python code/t039_log_excluded_datasets.py
python code/t040_create_comparison_report.py
python code/t041_generate_final_report.py
```

### 8. Verify Artifacts

```bash
python code/t048_verify_checksums_and_state.py
```

## Running the Full Pipeline

To run the entire pipeline in one go (excluding the main.py orchestration which is currently under repair):

```bash
python code/t011_ensure_data.py && \
python code/t012_run_baseline_analysis.py && \
python code/t013_record_baseline_metrics.py && \
python code/t022_save_cleaned_datasets.py && \
python code/t023_reanalyze_cleaned_variants.py && \
python code/t032_permutation_null_fpr.py && \
python code/t033_outlier_threshold_sweep.py && \
python code/t027_run_comparison.py && \
python code/t030_dataset_size_sensitivity.py && \
python code/t031_bootstrap_variance.py && \
python code/t034_generate_forest_plot.py && \
python code/t035_generate_ci_heatmap.py && \
python code/t036_pvalue_shift_reporting.py && \
python code/t037_ci_width_reporting.py && \
python code/t038_effect_size_reporting.py && \
python code/t039_log_excluded_datasets.py && \
python code/t040_create_comparison_report.py && \
python code/t041_generate_final_report.py && \
python code/t048_verify_checksums_and_state.py
```

## Output Artifacts

The pipeline produces the following artifacts in `data/processed/`:

- `baseline_metrics.json`: Baseline statistical metrics.
- `cleaned_metrics.json`: Metrics after applying cleaning strategies.
- `null_fpr_metrics.json`: False positive rate metrics from permutation tests.
- `outlier_threshold_sweep.json`: Results of the outlier threshold sweep (T033).
- `comparison_report.json`: Final comparison report.
- `final_report.txt`: Human-readable summary.

## Troubleshooting

- If `data/processed/` is empty, ensure `t011_ensure_data.py` ran successfully.
- If analysis scripts fail, check that `data/raw/` contains valid CSV files.
- Ensure all dependencies in `requirements.txt` are installed.
