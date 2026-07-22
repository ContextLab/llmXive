# Quickstart Guide

## Prerequisites
- Python 3.11
- `code/requirements.txt` dependencies installed

## Running the Pipeline

1. **Ingestion**: Fetch and merge raw data
 ```bash
 python code/scripts/run_ingestion.py
 ```
 (Note: If `run_ingestion.py` does not exist, use `python code/src/ingestion/ingest_pipeline.py`)

2. **Preprocessing**: Standardize, impute, filter, and save
 ```bash
 python code/scripts/run_preprocessing.py
 ```
 Output: `data/processed/alloys_raw.csv`

3. **Feature Engineering**: Calculate descriptors
 ```bash
 python code/scripts/run_feature_engineering.py
 ```
 Output: `data/processed/alloys_features.csv`

4. **Model Training**: Train and evaluate models
 ```bash
 python code/scripts/run_model_training.py
 ```
 Output: `data/processed/model_metrics.json`

5. **Validation & Reports**: Generate final reports
 ```bash
 python code/scripts/run_validation.py
 ```

## Output Artifacts
- `data/processed/alloys_raw.csv`
- `data/processed/alloys_features.csv`
- `data/processed/model_metrics.json`
- `docs/reports/final_report.md`