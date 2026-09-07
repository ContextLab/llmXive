# Quickstart Guide: Predicting the Impact of Cold Work on Recrystallization Kinetics

This guide provides a 5-step execution flow to run the full analysis pipeline from data generation to statistical validation.

## Prerequisites

- Python 3.9+
- `pip` installed
- Project root: `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/`

## Step 1: Setup Environment

Install dependencies:

```bash
cd projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/
pip install -r requirements.txt
```

## Step 2: Initialize Directory Structure

Ensure all required directories exist:

```bash
python code/setup_project_structure.py
python code/setup_data_dirs.py
python code/create_artifact_dirs.py
```

## Step 3: Generate Synthetic Baseline Data

Generate the primary synthetic dataset (T007) with seed=42:

```bash
python code/main.py --step generate
```

*Output*: `data/raw/synthetic_baseline.csv`, `data/raw/synthetic_baseline.csv.sha256`

## Step 4: Run the Full Pipeline

Execute the complete data processing, training, and evaluation workflow:

```bash
python code/main.py --step all
```

This single command performs the following sub-steps sequentially:
1. **Ingest**: Validates and filters raw data (`data/processed/validated.csv`).
2. **Engineer**: Calculates interaction features (`data/processed/engineered_features.csv`).
3. **Finalize**: Enforces row caps and saves final dataset (`data/processed/final_dataset.csv`).
4. **Train**: Trains the Random Forest model and saves metrics (`artifacts/models/kinetic_model.pkl`).
5. **Evaluate**: Runs permutation tests and SHAP analysis (`artifacts/reports/`).

## Step 5: Verify Outputs

Confirm that the following artifacts have been created:

- `data/processed/validated.csv`
- `data/processed/engineered_features.csv`
- `data/processed/final_dataset.csv`
- `artifacts/models/kinetic_model.pkl`
- `artifacts/reports/training_metrics.json`
- `artifacts/reports/statistical_significance.json`
- `artifacts/reports/shap_interaction_report.json`

You can inspect the metrics by reading the JSON files:

```bash
cat artifacts/reports/training_metrics.json
cat artifacts/reports/statistical_significance.json
```
