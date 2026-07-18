# Quickstart Guide: Predicting Molecular Descriptors from Quantum Chemical Calculations

This guide provides a 5-step pipeline to execute the end-to-end research workflow.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## 5-Step Pipeline Execution

Run the following commands in order to download data, extract features, train models, and generate analysis.

### Step 1: Download and Verify Data
Downloads the QM9 dataset from HuggingFace and validates integrity.
```bash
python code/01_data_download.py
```
*Outputs*: `data/raw/qm9_full.parquet`, `data/checksums.json`

### Step 2: Clean and Validate Molecules
Parses the raw data, filters invalid molecules, and saves the cleaned dataset.
```bash
python code/02_clean.py
```
*Outputs*: `data/processed/molecules_cleaned.parquet`

### Step 3: Extract Features (2D & 3D)
Generates Morgan fingerprints and 3D graph features, splits data, and handles memory constraints.
**Note**: This step is invoked via the `extract.py` wrapper to match the run-book.
```bash
python code/extract.py
```
*Outputs*: `data/processed/features_2d.npy`, `data/processed/features_3d.npy`, `data/processed/labels_train.csv`, `data/processed/labels_test.csv`, `data/processed/split_indices_train.json`, `data/processed/split_indices_test.json`

### Step 4: Train Models (2D & 3D)
Trains Random Forest Regressors using 5-fold cross-validation and grid search.
```bash
python code/train.py
```
*Outputs*: `artifacts/models/model_2d.pkl`, `artifacts/models/model_3d.pkl`, `artifacts/metrics/cv_metrics.json`, `artifacts/metrics/stability_report.json`

### Step 5: Analyze and Generate Report
Computes baselines, statistical tests, failure boundaries, and generates parity plots.
```bash
python code/analyze.py
```
*Outputs*: `artifacts/metrics/baseline_error.json`, `artifacts/metrics/test_predictions.json`, `artifacts/metrics/statistics.json`, `artifacts/metrics/failure_boundary.json`, `artifacts/plots/parity_2d.png`, `artifacts/plots/parity_3d.png`, `artifacts/report.md`

## Validation

After running the pipeline, verify all artifacts were generated:
```bash
python code/05_quickstart_validator.py
```
