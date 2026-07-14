# Quickstart Guide

This guide describes how to run the full analysis pipeline end-to-end.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Execution Steps

### 1. Download and Preprocess Data
```bash
python code/main.py --step download_preprocess --subjects 50
```
*Note: This step requires FSL/AFNI for full preprocessing. For CI validation, it uses synthetic data or nilearn fetch_adhd as a fallback.*

### 2. Extract Metrics
```bash
python code/main.py --step extract_metrics
```

### 3. Run Analysis (PCA, Correlations, FDR)
This step runs T023a (PCA), T023b (Merge), T024 (Correlations), T025 (FDR), and T027 (Logging).
```bash
python code/analysis/pca_runner.py
python code/analysis/create_full_metrics.py
python code/analysis/correlations.py
```
*Alternatively, run the unified analysis runner:*
```bash
python code/main.py --step analyze
```

### 4. Visualization and Reporting
```bash
python code/main.py --step viz_report
```

## Output Artifacts

- `data/analysis/pca_loadings.csv`: PCA component loadings (T023a)
- `data/analysis/factor_scores.csv`: Subject PCA factor scores (T023a)
- `data/analysis/full_metrics.csv`: Merged raw and PCA metrics (T023b)
- `data/analysis/correlation_results.csv`: Correlation statistics with FDR (T024, T025)
- `figures/`: Generated plots (T031, T032)
- `docs/report.md`: Final report (T033)
