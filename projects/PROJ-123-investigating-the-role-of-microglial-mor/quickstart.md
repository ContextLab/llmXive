# Quickstart Guide

## Prerequisites
- Python 3.11
- Install dependencies: `pip install -r requirements.txt`

## Generate Synthetic Data (for validation)
```bash
python code/main.py --mode generate-synthetic --output data/processed/synthetic_dataset.csv
```

## Run Full Pipeline
This command generates synthetic data (if not present), runs analysis, and produces reports.
```bash
python code/main.py --mode run-full
```

## Run Specific Steps
- **Analysis Only**: `python code/main.py --mode run-analysis`
- **Report Only**: `python code/main.py --mode run-report`
- **Validation Only**: `python code/main.py --mode run-validation`

## Output Files
- `data/processed/synthetic_dataset.csv`: Synthetic input data
- `data/processed/morphological_metrics.csv`: Extracted morphological metrics (T018)
- `data/intermediates/vif_check.json`: VIF scores and PCA trigger status (T026)
- `data/intermediates/pca_model.pkl`: Fitted PCA model or identity wrapper (T026)
- `reports/regression_results.json`: Regression results
- `reports/regression_results.md`: Human-readable report
- `reports/validation_report.md`: Validation metrics