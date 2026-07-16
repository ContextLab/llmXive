# Quickstart Guide

This guide walks you through running the full pipeline from data download to final analysis.

## Prerequisites
- Python 3.11+
- ~14 GB free disk space (for QM9 dataset and features)
- ~8 GB RAM (pipeline will auto-downsample if necessary)

## Step 1: Environment Setup
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Run the Pipeline
Execute the scripts in order. Each script writes artifacts to the `data/` or `artifacts/` directories.

### 2.1 Download and Validate Data
```bash
python code/01_data_download.py
```
**Outputs**:
- `data/raw/qm9_full.parquet`
- `data/checksums.json`
- `data/processed/molecules_cleaned.parquet`

### 2.2 Extract Features
```bash
python code/02_feature_extraction.py
```
**Outputs**:
- `data/processed/features_2d.npy`
- `data/processed/features_3d.npy`
- `data/processed/labels.csv`

### 2.3 Train Models
```bash
python code/03_model_training.py
```
**Outputs**:
- `artifacts/models/model_2d.pkl`
- `artifacts/models/model_3d.pkl`
- `artifacts/metrics/cv_metrics.json`
- `artifacts/metrics/stability_report.json`

### 2.4 Analysis and Reporting
```bash
python code/04_analysis.py
```
**Outputs**:
- `artifacts/metrics/baseline_error.json`
- `artifacts/metrics/test_predictions.json`
- `artifacts/metrics/statistics.json`
- `artifacts/metrics/failure_boundary.json`
- `artifacts/plots/parity_2d.png`
- `artifacts/plots/parity_3d.png`
- `artifacts/report.md`

## Step 3: Validation
Run the quickstart validator to ensure all artifacts were generated correctly:
```bash
python code/05_quickstart_validator.py
```
This script checks for the existence and integrity of all required files.

## Troubleshooting
- **Memory Error**: If you encounter memory issues, the pipeline automatically downsamples. Ensure your system has at least 6.5 GB RAM available.
- **RDKit Errors**: Ensure `rdkit` is installed and `LD_LIBRARY_PATH` is set correctly if running on Linux.
- **HuggingFace Connection**: If `download_qm9_dataset` fails, check your internet connection and ensure you can access `huggingface.co`.
