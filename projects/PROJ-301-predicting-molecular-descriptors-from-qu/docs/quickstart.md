# Quickstart Guide: Predicting Molecular Descriptors from Quantum Chemical Calculations

This guide provides a 5-step pipeline to download QM9 data, extract features, train models, and analyze failure boundaries.

## Prerequisites

- Python 3.11+
- pip
- Git

## Step 1: Setup Environment

```bash
# Create virtual environment
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Download and Clean Data

```bash
# Download QM9 dataset from HuggingFace
python code/01_data_download.py

# Clean and validate the dataset
python code/02_clean.py
```

## Step 3: Extract Features

```bash
# Extract 2D and 3D features from cleaned molecules
python code/03_feature_extraction.py
```

## Step 4: Train Models

```bash
# Train Random Forest models on 2D and 3D features
python code/04_train_orchestrator.py
```

## Step 5: Analyze Results

```bash
# Run full analysis pipeline (baselines, predictions, statistics, failure boundaries, plots)
python code/analyze.py
```

## Verification

Run the validator to ensure all artifacts were created:

```bash
python code/05_quickstart_validator.py
```

## Expected Artifacts

After successful execution, the following files should exist:

- `data/raw/qm9_full.parquet`
- `data/processed/molecules_cleaned.parquet`
- `data/processed/features_2d.npy`
- `data/processed/features_3d.npy`
- `data/processed/labels_train.csv`
- `data/processed/labels_test.csv`
- `artifacts/models/model_2d.pkl`
- `artifacts/models/model_3d.pkl`
- `artifacts/metrics/cv_metrics.json`
- `artifacts/plots/parity_2d.png`
- `artifacts/plots/parity_3d.png`
- `artifacts/report.md`
