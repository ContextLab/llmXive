# Quickstart Guide

This guide outlines the steps to run the full analysis pipeline for PROJ-284.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`

## Step-by-Step Execution

### 1. Setup and Data Download
Run the download and preprocessing pipeline.
```bash
python code/main.py --step download_preprocess --subjects 50
```

### 2. Extract Metrics
Calculate graph metrics and aggregate them.
```bash
python code/main.py --step metrics
```

### 3. Run Analysis (PCA, Correlations, FDR)
This step performs PCA, calculates correlations with FD covariate, applies Benjamini-Hochberg FDR correction, and saves all results including `factor_scores.csv`.
```bash
python code/main.py --step correlations
```

### 4. Visualization and Reporting
Generate scatter plots, network diagrams, and the final report.
```bash
python code/main.py --step viz_report
```

## Output Artifacts

- `data/processed/aggregated_metrics.csv`: Aggregated node-level metrics.
- `data/analysis/pca_loadings.csv`: PCA component loadings.
- `data/analysis/factor_scores.csv`: Subject-level PCA factor scores.
- `data/analysis/full_metrics.csv`: Merged raw metrics and PCA scores.
- `data/analysis/correlation_results.csv`: Correlation results with FDR correction.
- `figures/*.png`: Generated plots.
- `docs/report.md`: Final analysis report.
