# Quickstart Guide: Predicting Molecular Descriptors from Quantum Chemical Calculations

This guide provides a 5-step end-to-end execution of the pipeline to predict molecular descriptors (dipole, HOMO, LUMO) from the QM9 dataset using machine learning.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Step 1: Project Setup

Ensure the directory structure exists:

```bash
python code/setup_project_structure.py
```

## Step 2: Data Acquisition

Download and verify the QM9 dataset from the HuggingFace Hub.

```bash
python code/01_data_download.py
```

*Expected Output*: `data/raw/qm9_full.parquet` and `data/checksums.json`

## Step 3: Data Cleaning

Parse, validate, and filter the raw dataset.

```bash
python code/02_clean.py
```

*Expected Output*: `data/processed/molecules_cleaned.parquet`

## Step 4: Feature Extraction

Generate 2D fingerprints and 3D graph features.

```bash
python code/03_feature_extraction.py
```

*Expected Output*: `data/processed/features_2d.npy`, `data/processed/features_3d.npy`, `data/processed/labels_train.csv`, `data/processed/labels_test.csv`

## Step 5: Model Training

Train Random Forest models on 2D and 3D features with 5-fold cross-validation.

```bash
python code/train_models.py
```

*Expected Output*: `artifacts/models/model_2d.pkl`, `artifacts/models/model_3d.pkl`, `artifacts/metrics/cv_metrics.json`

## Step 6: Analysis & Reporting

Generate predictions, statistical tests, and the final report.

```bash
python code/analyze_results.py
```

*Expected Output*: `artifacts/plots/parity_2d.png`, `artifacts/plots/parity_3d.png`, `artifacts/report.md`

## Validation

Run the validator to ensure all artifacts are present and the run-book is consistent.

```bash
python code/05_quickstart_validator.py
```