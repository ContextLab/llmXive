# Quickstart: Predicting Glass Forming Regions

This guide describes how to execute the research pipeline to predict the critical cooling rate (CCR) of ternary alloys.

## Environment Setup
```bash
# Clone and enter project
git clone <repo_url>
cd predict-glass-forming-region

# Setup virtualenv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execution Pipeline

### 1. Data Ingestion & Engineering
Downloads OQMD properties and the CCR dataset, computes descriptors, and filters for valid entries.
```bash
python src/data_pipeline/ingestion.py
```
- **Check**: Ensure `data/processed/processed_alloys.csv` contains $\ge 500$ rows.
- **Logs**: Check `data/logs/exclusion_log.txt` for filtered entries.

### 2. Model Training
Trains the Random Forest regressor and performs 5-fold cross-validation.
```bash
python src/models/trainer.py
```
- **Output**: `data/models/random_forest_model.pkl` and `data/models/cv_metrics.json`.

### 3. Analysis & Sensitivity
Calculates permutation importance and tests the model against different binary thresholds.
```bash
python src/models/evaluator.py
```
- **Output**: `data/reports/feature_importance.csv` and `data/reports/sensitivity_report.json`.

### 4. Validation
Validates all generated artifacts against their formal YAML contracts.
```bash
python src/data_pipeline/validation.py
```
- **Requirement**: Must output "All schemas validated - 0 errors."

## Reproducibility
To reset the pipeline and re-run from scratch:
```bash
rm -rf data/processed/* data/models/* data/reports/*
python src/data_pipeline/ingestion.py
python src/models/trainer.py
python src/models/evaluator.py
python src/data_pipeline/validation.py
```
