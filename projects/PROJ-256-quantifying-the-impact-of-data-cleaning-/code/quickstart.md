# llmXive Research Pipeline - Quickstart Guide

This guide explains how to run the full research pipeline to quantify the impact of data cleaning on statistical inference.

## Prerequisites

- Python 3.11+
- All dependencies installed via `pip install -r requirements.txt`

## Project Structure

```
.
├── code/ # Source code
│ ├── utils.py # Utility functions
│ ├── config.py # Configuration management
│ ├── models.py # Data models
│ ├── data_loader.py # Data acquisition
│ ├── cleaning.py # Cleaning strategies
│ ├── analysis.py # Statistical analysis
│ ├── reporting.py # Metrics comparison
│ └── main.py # Pipeline orchestrator
├── data/
│ ├── raw/ # Original downloaded datasets
│ └── processed/ # Cleaned data and analysis results
├── tests/ # Test suites
└── docs/ # Documentation
```

## Running the Pipeline

The pipeline consists of several sequential steps. You can run them individually or use the main orchestrator.

### Step 1: Ensure Data Exists (T011)

Download or verify the presence of raw datasets.

```bash
python code/t011_ensure_data.py
```

This script will:
- Attempt to download datasets from OpenML or UCI
- Validate checksums
- Store files in `data/raw/`

### Step 2: Run Baseline Analysis (T012)

Perform statistical analysis on raw, uncleaned data.

```bash
python code/t012_run_baseline_analysis.py
```

This script will:
- Load all datasets from `data/raw/`
- Run t-tests and linear regressions
- Output `data/processed/baseline_metrics.json`

### Step 3: Record Baseline Metrics (T013)

Aggregate and format baseline results.

```bash
python code/t013_record_baseline_metrics.py
```

This script will:
- Read baseline analysis results
- Format metrics with ≥3 decimal precision
- Write `data/processed/baseline_metrics.json`

### Step 4: Apply Cleaning Strategies (T017-T022)

Apply outlier removal and imputation strategies.

```bash
python code/t022_save_cleaned_datasets.py
```

This script will:
- Apply IQR outlier removal
- Apply mean/median/KNN imputation
- Save cleaned variants to `data/processed/`

### Step 5: Re-analyze Cleaned Data (T023)

Run statistical tests on cleaned datasets.

```bash
python code/t023_reanalyze_cleaned_variants.py
```

This script will:
- Load cleaned datasets
- Run identical tests as baseline
- Output `data/processed/cleaned_metrics.json`

### Step 6: Generate Null Datasets for FPR (T032)

Create permutation-based null datasets.

```bash
python code/t032_permutation_null_fpr.py
```

This script will:
- Shuffle outcome variables
- Run analysis on null data
- Output `data/processed/null_fpr_metrics.json`

### Step 7: Run Full Comparison (T027)

Compare baseline vs cleaned metrics.

```bash
python code/t027_run_comparison.py
```

### Step 8: Generate Visualizations (T034-T035)

Create forest plots and heatmaps.

```bash
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py
```

### Step 9: Generate Final Report (T041)

Aggregate all results into a final summary.

```bash
python code/t041_generate_final_report.py
```

## Running the Full Pipeline

You can also run the entire pipeline via the main orchestrator:

```bash
python code/main.py
```

This will execute all steps in the correct order.

## Expected Artifacts

After successful execution, the following files should exist:

- `data/raw/*.csv` - Original datasets
- `data/processed/baseline_metrics.json` - Baseline analysis results
- `data/processed/cleaned_metrics.json` - Cleaned data analysis results
- `data/processed/null_fpr_metrics.json` - Null dataset FPR estimates
- `figures/*.png` - Visualization outputs
- `output/final_report.md` - Final research report

## Troubleshooting

If you encounter errors:

1. Check that all dependencies are installed: `pip install -r requirements.txt`
2. Verify data exists in `data/raw/`
3. Check log output for specific error messages
4. Ensure environment variables are set correctly (see `.env.example`)

## Validation

Run the validation script to verify all artifacts:

```bash
python code/run_quickstart_validation.py
```
