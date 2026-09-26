# Quickstart Guide

This guide ensures the pipeline runs end-to-end and produces all declared artifacts.

## Prerequisites
- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`

## Execution Steps

### 1. Setup & Ingestion (T012 - T016)
This step downloads data (if needed), cleans it, and generates the intermediate dataset.
```bash
python code/ingestion.py
# T016 is triggered implicitly by the pipeline or run separately if needed
python code/t016_create_cleaned_dataset.py
```

### 2. Feature Extraction (T022 - T025)
Computes linguistic features and statistical tests.
```bash
python code/features.py --input data/interim/cleaned_adress.csv --output data/processed/features.csv
python code/stats.py --input data/processed/features.csv --output data/processed/stats_results.json
```

### 3. Modeling (T033 - T040)
Trains and validates models.
```bash
python code/modeling.py --input data/processed/features.csv --output data/processed/model_results.json
```

### 4. Verification
Run contract tests to verify artifacts.
```bash
pytest tests/contract/test_schemas.py
```

## Expected Artifacts
- `data/interim/cleaned_adress.csv`
- `data/processed/features.csv`
- `data/results/metadata.json`
- `data/results/statistical_metrics.json`
- `data/results/model_performance.json`