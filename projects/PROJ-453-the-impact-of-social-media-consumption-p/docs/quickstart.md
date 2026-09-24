# Quick Start Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r code/requirements.txt
```

## Running the Full Pipeline
Execute the following commands in order:

1. **Feasibility Check**:
 ```bash
 python code/00_feasibility_check.py
 ```

2. **Ingestion**:
 ```bash
 python code/01_ingest.py
 ```

3. **Variable Engineering**:
 ```bash
 python code/02_engineer.py
 ```

4. **Model Fitting**:
 ```bash
 python code/03_model.py
 ```

5. **Visualization**:
 ```bash
 python code/04_visualize.py
 ```

## Expected Outputs
- `data/processed/participants_cleaned.csv`
- `results/models/regression_summary.json`
- `results/figures/regression_plot.png`
- `results/final_report.json`

## Troubleshooting
- If `No raw CSV files found` error occurs, ensure `data/raw/` contains downloaded datasets.
- If `AttributeError: module 'statsmodels.api' has no attribute 'OLSResults'`, ensure `statsmodels` is updated.
