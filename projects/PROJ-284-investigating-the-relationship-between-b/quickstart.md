# Quickstart Guide

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline

The pipeline is executed in steps. Each step produces specific artifacts.

### Step 1: Download & Preprocess
Downloads HCP/ADHD data and performs preprocessing (or synthetic validation).
```bash
python code/main.py --step download_preprocess --subjects 50
```
**Output**: `data/processed/` (NIfTI files, aggregated metrics)

### Step 2: Extract Metrics
Extracts network metrics and generates full metrics dataframe.
```bash
python code/main.py --step metrics
```
**Output**: `data/analysis/full_metrics.csv`, `data/analysis/pca_loadings.csv`

### Step 3: Correlations
Performs correlation analysis with covariates and FDR correction.
```bash
python code/main.py --step correlations
```
**Output**: `data/analysis/correlations.csv`

### Step 4: Visualization & Report
Generates plots and the final report.
```bash
python code/main.py --step viz_report
```
**Output**: `figures/*.png`, `docs/report.md`

## Full Run (End-to-End)
To run the entire pipeline:
```bash
python code/main.py --step all
```

## Validation
Verify outputs:
- `data/analysis/full_metrics.csv` exists
- `data/analysis/correlations.csv` exists
- `figures/scatter_plot_*.png` exist
- `docs/report.md` exists