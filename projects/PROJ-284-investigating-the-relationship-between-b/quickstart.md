# Quick Start Guide

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Execution Steps

### 1. Data Download & Preprocessing (Simulated for CI)
```bash
python code/main.py --step download_preprocess --subjects 50
```

### 2. Metric Extraction
```bash
python code/main.py --step metrics
```

### 3. Analysis (PCA, Correlations, Full Metrics)
```bash
python code/main.py --step correlations
```

### 4. Visualization & Report
```bash
python code/main.py --step viz_report
```

## Output Artifacts
- `data/processed/aggregated_metrics.csv`
- `data/analysis/pca_loadings.csv`
- `data/analysis/factor_scores.csv`
- `data/analysis/full_metrics.csv`
- `data/analysis/correlations.csv`
- `figures/*.png`
- `docs/report.md`
