# Quickstart Guide

This guide demonstrates how to run the full pipeline for the Statistical Analysis of Publicly Available Chess Game Data.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Step-by-Step Execution

### 1. Data Download
Download a subset of Lichess games.
```bash
python code/src/data/download.py
```

### 2. Data Processing
Parse PGNs, extract features, and calculate outcome deviations.
```bash
python code/src/data/parse.py
python code/src/data/process.py
```

### 3. Model Fitting
Fit Beta and Ridge regression models.
```bash
python code/src/models/fit.py
```

### 4. Metrics Calculation
Calculate p-values and apply FDR correction.
```bash
python code/src/models/metrics.py
```

### 5. Cross-Validation
Perform k-fold cross-validation.
```bash
python code/src/models/validate.py
```

### 6. Sensitivity Analysis (Task T025)
Perform threshold sweep analysis on p-values.
```bash
python code/src/reports/sensitivity.py
```

### 7. Validation
Validate the final dataset against contracts.
```bash
python code/src/validation/validate_contracts.py --data data/processed/games.parquet
```

## Expected Outputs

- `data/processed/games.parquet`: Cleaned game records.
- `data/results/model_metrics.json`: Model coefficients and metrics.
- `data/results/sensitivity_analysis.json`: Sensitivity analysis results (T025).
- `data/results/diagnostics.json`: Diagnostic report.
