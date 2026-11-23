# Quickstart Guide

## Prerequisites
- Python 3.8+
- Virtual environment activated

## Installation
1. Install dependencies:
 `pip install -r requirements.txt`

## Data Ingestion (Phase 3)
Run the data loader to fetch and verify the dataset:
`python code/data_loader.py --verify`

## Preprocessing (User Story 1)
Run the preprocessing pipeline to generate precursor metrics:
`python code/preprocess.py --input-dir data/raw/ --output-dir data/processed/`

## Statistical Analysis (User Story 2)
Run the analysis pipeline to aggregate shear bands and perform KS tests:
`python code/analysis.py --input-dir data/processed/ --output-dir data/processed/`

## Prediction (User Story 3)
Run the prediction pipeline to derive thresholds and perform sensitivity analysis:
`python code/predict.py --input-dir data/processed/ --output-dir data/processed/`

## Verification
Check that all output files are generated in `data/processed/`:
- `precursor_metrics.csv`
- `yield_flags.json`
- `shear_band_aggregation.csv`
- `ks_test_results.json`
- `histograms.png`
- `sensitivity_table.csv`
- `prediction_results.json`
- `performance_report.json`