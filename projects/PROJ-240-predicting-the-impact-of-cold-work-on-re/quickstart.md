# Quickstart Guide: Predicting the Impact of Cold Work on Recrystallization Kinetics

This guide provides a 5-step execution path to run the full analysis pipeline on the `PROJ-240` project.
Ensure you are in the project root directory (`projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/`).

## Prerequisites
- Python 3.9+
- `pip` package manager

## Step 1: Install Dependencies
Install all required Python packages listed in `requirements.txt`.
```bash
pip install -r requirements.txt
```

## Step 2: Generate Synthetic Baseline Data
Generate the deterministic synthetic dataset (seed=42) with exactly 10,000 rows.
This creates `data/raw/synthetic_baseline.csv` and its SHA-256 checksum.
```bash
python code/generate_synthetic.py
```

## Step 3: Ingest and Engineer Features
Load the synthetic data, validate physical bounds, impute missing values, clip outliers,
and engineer interaction features (e.g., `cold_work_Mn_content`).
This produces `data/processed/final_dataset.csv`.
```bash
python code/ingest.py
python code/engineer.py
```

## Step 4: Train Predictive Model
Split the data, train a Random Forest Regressor (CPU-only), perform 5-fold cross-validation,
and evaluate on a held-out test set.
This saves the model to `artifacts/models/kinetic_model.pkl` and metrics to `artifacts/reports/training_metrics.json`.
```bash
python code/train.py
```

## Step 5: Evaluate Statistical Significance
Run the permutation test to compare the Interaction Model against an Additive baseline
and compute SHAP interaction values to identify key drivers.
This generates `artifacts/reports/statistical_significance.json` and `artifacts/reports/shap_interaction_report.json`.
```bash
python code/evaluate.py
```

## Verification
Upon successful completion, the following artifacts should exist:
- `data/raw/synthetic_baseline.csv`
- `data/processed/final_dataset.csv`
- `artifacts/models/kinetic_model.pkl`
- `artifacts/reports/training_metrics.json`
- `artifacts/reports/statistical_significance.json`
- `artifacts/reports/shap_interaction_report.json`