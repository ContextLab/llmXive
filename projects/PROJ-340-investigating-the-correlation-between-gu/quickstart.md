# Quickstart Guide

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Generate Synthetic Data
```bash
python code/generate_synthetic_data.py --n-samples 100 --output data/raw/synthetic_data.csv --manifest data/metadata/synthetic_data_manifest.json
```

## 3. Run Ingestion and Filtering (T012, T013, T014b)
```bash
python code/ingest.py --mode synthetic --input data/raw/synthetic_data.csv --output data/processed/filtered_data.parquet --config data/config/required_variables.yaml
```

## 4. Run Full Analysis Pipeline
```bash
python code/main.py --input data/processed/filtered_data.parquet --output data/results/
```

## 5. Verify Artifacts
Ensure the following files exist:
- `data/raw/synthetic_data.csv`
- `data/metadata/synthetic_data_manifest.json`
- `data/processed/filtered_data.parquet`
- `data/results/variable_load_metrics.json`
- `data/results/correlation_matrix.json`
- `data/results/collinearity_report.json`
- `data/results/sensitivity_analysis.json`
- `data/results/timing_evidence.json`