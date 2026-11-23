# Quickstart Guide

## Prerequisites
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Execution
Run the full pipeline:
```bash
python code/main.py
```

This will execute:
1. Ingestion (T013) -> `data/raw/medmis_subset.csv`
2. Feature Extraction (T014) -> `data/processed/features.csv`
3. Human Pilot (T017)
4. Inference & Labeling (T020-T025)
5. Modeling (T029-T035)

## Outputs
- `data/raw/medmis_subset.csv`: Raw dataset
- `data/processed/features.csv`: Extracted features
- `data/results/regression_results_raw.csv`: Final model results
