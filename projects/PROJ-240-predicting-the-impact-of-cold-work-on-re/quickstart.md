# Quickstart Guide: Predicting the Impact of Cold Work on Recrystallization Kinetics

This guide provides a 5-step execution process to run the full pipeline.

## Prerequisites
- Python 3.9+
- `pip`

## Step 1: Install Dependencies
```bash
cd projects/PROJ-240-predicting-the-impact-of-cold-work-on-re
pip install -r requirements.txt
```

## Step 2: Generate Synthetic Data
Generates the baseline dataset with seed=42.
```bash
python code/generate_synthetic.py
```
*Output*: `data/raw/synthetic_baseline.csv`

## Step 3: Ingest & Engineer Features
Loads data, validates, clips outliers, and engineers interaction features.
```bash
python code/ingest.py
python code/engineer.py
```
*Outputs*: `data/processed/validated.csv`, `data/processed/engineered_features.csv`

## Step 4: Train Models
Splits data, trains Interaction and Additive models, and evaluates.
```bash
python code/train.py
```
*Outputs*: `artifacts/models/kinetic_model.pkl`, `artifacts/models/additive_model.pkl`, `artifacts/reports/training_metrics.json`

## Step 5: Evaluate & Analyze
Runs permutation tests, SHAP analysis, and generates the final statistical report.
```bash
python code/evaluate.py
```
*Output*: `artifacts/reports/statistical_significance.json`

## Full Pipeline
Alternatively, run the entire pipeline at once:
```bash
python code/main.py
```