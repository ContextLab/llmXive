# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip
- git

## Setup
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Acquisition
Run the download and preprocessing step (requires HCP credentials or uses synthetic fallback):
```bash
python code/main.py --step download_preprocess --subjects 50
```

## Metric Extraction
Extract graph metrics and aggregate them:
```bash
python code/main.py --step metrics
```

## Analysis (Correlation & FDR)
Run the full correlation analysis, PCA, and Benjamini-Hochberg FDR correction.
This step produces `data/analysis/full_metrics.csv`.
```bash
python code/analysis/run_analysis.py
```

## Visualization & Reporting
Generate plots and the final report:
```bash
python code/main.py --step viz_report
```

## Validation
Run the validation suite:
```bash
python code/tools/validate_quickstart.py
```
