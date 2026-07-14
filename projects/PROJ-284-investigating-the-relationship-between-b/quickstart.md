# Quickstart Guide

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Execution Steps

### 1. Download Data
Fetches the ADHD dataset from Nilearn.
```bash
python code/data/download.py
```

### 2. Extract Metrics
Processes subjects to calculate graph metrics.
```bash
python code/data/metrics.py
```

### 3. Run Analysis (PCA, Correlations, Full Metrics)
Executes PCA, correlations, FDR correction, and generates the full metrics file.
```bash
python code/analysis/pca_runner.py
```

### 4. Visualization and Reporting
Generates plots and the final report.
```bash
python code/viz/scatter.py
python code/report/generate.py
```

## Expected Outputs
- `data/raw/phenotypic_adhd.csv`
- `data/processed/aggregated_metrics.csv`
- `data/analysis/pca_loadings.csv`
- `data/analysis/factor_scores.csv`
- `data/analysis/correlations.csv`
- `data/analysis/full_metrics.csv`