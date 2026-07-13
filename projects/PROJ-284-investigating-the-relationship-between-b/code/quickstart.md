# Quickstart Guide

This guide outlines the steps to run the full pipeline for the project.

## Prerequisites

- Python 3.11
- Dependencies installed: `pip install -r requirements.txt`
- HCP Credentials configured in environment variables (see `code/config.py`)

## Execution Steps

### 1. Setup and Configuration
Ensure the project structure is initialized:
```bash
python code/setup_project_structure.py
```

### 2. Data Download and Preprocessing
Download and preprocess HCP data (T012-T017).
Note: This step requires FSL/AFNI for full preprocessing. If not available, it will run validation on synthetic data or skip heavy preprocessing if configured.
```bash
python code/main.py --step download_preprocess --subjects 50
```

### 3. Metric Extraction
Extract time-series and calculate graph metrics (T020-T022).
```bash
python code/main.py --step extract_metrics
```

### 4. Correlation Analysis (T023a, T023b, T024-T028)
Run PCA, merge metrics, and perform correlation analysis.
This step generates `data/analysis/pca_loadings.csv`, `data/analysis/factor_scores.csv`, and `data/analysis/full_metrics.csv`.
```bash
python code/analysis/correlations_main_runner.py
```

### 5. Visualization and Reporting (T031-T033)
Generate plots and the final report.
```bash
python code/main.py --step viz_report
```

## Verification
Check that the following files exist after successful execution:
- `data/analysis/pca_loadings.csv`
- `data/analysis/factor_scores.csv`
- `data/analysis/full_metrics.csv`
- `data/analysis/correlation_results.csv` (from T024)
- `figures/` directory with generated plots
- `docs/report.md`

## Troubleshooting
- If `nilearn` import errors occur, ensure `nilearn` is installed and compatible with your Python version.
- Check `logs/pipeline.log` for detailed error messages.
- Ensure HCP credentials are set if downloading real data.
