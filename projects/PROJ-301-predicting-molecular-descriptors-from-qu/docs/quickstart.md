# Quickstart Guide: Predicting Molecular Descriptors from Quantum Chemical Calculations

This guide provides a 5-step execution flow to run the full pipeline end-to-end.
It assumes you have already created the project structure (T001) and installed dependencies (T002).

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Step 1: Setup Project Structure (One-time)

Ensure the directory structure exists:

```bash
python code/setup_project_structure.py
```

## Step 2: Download and Clean Data

Download the QM9 dataset from the verified HuggingFace source and clean it.

```bash
python code/01_data_download.py
python code/02_clean.py
```

*Note: These steps generate `data/raw/qm9_full.parquet` and `data/processed/molecules_cleaned.parquet`.*

## Step 3: Feature Extraction

Generate 2D and 3D features from the cleaned data.

```bash
python code/03_feature_extraction.py
```

*Note: This step generates `data/processed/features_2d.npy`, `data/processed/features_3d.npy`, and label CSVs.*

## Step 4: Model Training

Train Random Forest models on 2D and 3D features using 5-fold cross-validation.

```bash
python code/train_models.py
```

*Note: This command invokes `code/04_model_training.py` to train models and save artifacts to `artifacts/models/` and `artifacts/metrics/`.*

## Step 5: Analysis and Reporting

Perform comparative analysis, generate parity plots, and identify failure boundaries.

```bash
python code/analyze.py
```

*Note: This command orchestrates `code/05_analysis.py` to generate the final report and plots in `artifacts/`.*

## Validation

Verify that all expected artifacts have been generated:

```bash
python code/05_quickstart_validator.py
```

## Troubleshooting

- **Dataset Not Found**: Ensure you have network access to HuggingFace Hub.
- **Memory Errors**: The pipeline includes a memory monitor (T004) that triggers downsampling if usage exceeds 6.5 GB.
- **Import Errors**: Ensure you are running scripts from the project root and that `code/` is in your `PYTHONPATH`.
