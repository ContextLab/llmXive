# Quickstart Guide

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Execution Steps

### 1. Data Acquisition & Preprocessing
```bash
python code/main.py --step download_preprocess --subjects 50
```

### 2. Metric Extraction
```bash
python code/main.py --step extract_metrics
```

### 3. Analysis (PCA & Correlations)
This step runs:
- PCA on network metrics (produces `data/analysis/pca_loadings.csv`, `data/analysis/factor_scores.csv`)
- Merges metrics with PCA scores (produces `data/analysis/full_metrics.csv`)
- Runs Spearman/Pearson correlations with FD covariate (produces `data/analysis/correlation_results.csv`)
```bash
python code/main.py --step analyze
```

### 4. Visualization & Reporting
```bash
python code/main.py --step viz_report
```

## Output Artifacts
- `data/analysis/pca_loadings.csv`
- `data/analysis/factor_scores.csv`
- `data/analysis/full_metrics.csv`
- `data/analysis/correlation_results.csv`
- `figures/*.png`
- `docs/report.md`