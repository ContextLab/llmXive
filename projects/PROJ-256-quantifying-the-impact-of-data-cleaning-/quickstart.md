# Quickstart Guide

This guide walks you through running the full data cleaning impact analysis pipeline.

## Prerequisites

- Python 3.11+
- All dependencies installed (see `requirements.txt`)

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline consists of several sequential steps. Run them in order:

### Step 1: Ensure Data Exists

Download or verify the existence of raw datasets.

```bash
python code/t011_ensure_data.py
```

### Step 2: Run Baseline Analysis

Analyze raw, uncleaned datasets to establish baseline metrics.

```bash
python code/t012_run_baseline_analysis.py
```

This produces: `data/processed/baseline_metrics.json`

### Step 3: Record Baseline Metrics

Format and record baseline metrics for comparison.

```bash
python code/t013_record_baseline_metrics.py
```

### Step 4: Apply Cleaning Strategies

Apply various cleaning strategies (outlier removal, imputation, recoding).

```bash
python code/t022_save_cleaned_datasets.py
```

### Step 5: Re-analyze Cleaned Variants

Run statistical tests on cleaned datasets.

```bash
python code/t023_reanalyze_cleaned_variants.py
```

This produces: `data/processed/cleaned_metrics.json`

### Step 6: Run Comparison Analysis

Compare baseline and cleaned metrics.

```bash
python code/t027_run_comparison.py
```

### Step 7: Generate Visualizations

Create forest plots and heatmaps.

```bash
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py
```

### Step 8: Generate Final Report

Aggregate all results into a final report.

```bash
python code/t041_generate_final_report.py
```

## Full Pipeline Execution

To run the entire pipeline in sequence:

```bash
# Run all steps
python code/t011_ensure_data.py && \
python code/t012_run_baseline_analysis.py && \
python code/t013_record_baseline_metrics.py && \
python code/t022_save_cleaned_datasets.py && \
python code/t023_reanalyze_cleaned_variants.py && \
python code/t027_run_comparison.py && \
python code/t034_generate_forest_plot.py && \
python code/t035_generate_ci_heatmap.py && \
python code/t041_generate_final_report.py
```

## Validating Results

After running the pipeline, verify that the following artifacts exist:

- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/comparison_report.json`
- `figures/forest_plot.png`
- `figures/ci_heatmap.png`
- `output/final_report.txt`

## Troubleshooting

If you encounter errors:

1. Check that all dependencies are installed: `pip install -r requirements.txt`
2. Verify that raw data exists in `data/raw/`
3. Check log files for detailed error messages
4. Ensure file paths are correct and writable

## Output Files

- `data/processed/baseline_metrics.json`: Baseline statistical metrics
- `data/processed/cleaned_metrics.json`: Metrics after cleaning
- `data/processed/comparison_report.json`: Comparison analysis
- `figures/forest_plot.png`: Visualization of p-value shifts
- `figures/ci_heatmap.png`: Heatmap of CI width changes
- `output/final_report.txt`: Comprehensive final report
