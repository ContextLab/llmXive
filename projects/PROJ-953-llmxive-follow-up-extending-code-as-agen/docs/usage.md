# Usage Guide

## Prerequisites

- Python 3.11+
- pip dependencies installed from `requirements.txt`

## Pipeline Steps

### 1. Data Ingestion
Run `code/scripts/ingest.py` to download SWE-bench and AgentBench subsets from HuggingFace and generate `data/processed/ground_truth.csv`.

### 2. Feature Extraction
Run `code/scripts/extract_features.py` to parse code diffs, build dependency graphs, and calculate structural metrics. Output: `data/processed/features.csv` and `data/graphs/{task_id}.json`.

### 3. Model Training
Run `code/scripts/train_model.py` to train predictive models and perform sensitivity analysis. Output: `models/decision_boundary.pkl` and `data/processed/threshold_sweep.json`.

### 4. Report Generation
Run `code/scripts/generate_model_report.py` to produce `data/processed/model_report.json`.

## Validation

Run `python code/scripts/validate_features.py` to ensure all metrics are present and valid.
