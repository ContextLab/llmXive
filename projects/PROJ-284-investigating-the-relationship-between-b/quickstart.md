# Quickstart Guide

This guide walks you through running the full analysis pipeline for PROJ-284.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline

### Step 1: Data Acquisition and Preprocessing

```bash
python code/main.py --step download_preprocess --subjects 50
```

This downloads HCP data (or ADHD dataset as fallback) and preprocesses it.

### Step 2: Metric Extraction

```bash
python code/main.py --step metrics
```

This extracts functional connectivity matrices and graph metrics.

### Step 3: Correlation Analysis (PCA + FDR)

```bash
python code/analysis/pca_runner.py
python code/analysis/create_full_metrics.py
python code/analysis/correlations.py
```

This performs:
1. PCA on network metrics (T023a) -> `data/analysis/factor_scores.csv`
2. Merge metrics with PCA scores (T023b) -> `data/analysis/full_metrics.csv`
3. Correlation with FD covariate and FDR correction (T024, T025) -> `data/analysis/correlations.csv`

### Step 4: Visualization and Reporting

```bash
python code/main.py --step viz_report
```

This generates scatter plots and the final report.

## Expected Outputs

After a successful run, you should have:

- `data/analysis/factor_scores.csv`: PCA factor scores per subject
- `data/analysis/full_metrics.csv`: All raw metrics + PCA factors
- `data/analysis/correlations.csv`: Correlation results with FDR correction
- `figures/`: Generated plots
- `docs/report.md`: Final analysis report

## Troubleshooting

If you encounter errors, check:
1. All dependencies are installed
2. Data files exist in `data/raw` and `data/processed`
3. Configuration in `code/config.py` is valid
