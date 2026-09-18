# Quickstart Guide

This guide outlines the steps to run the full pipeline for predicting molecular conductivity.

## Prerequisites

- Python 3.11+
- Virtual environment activated

## Installation

```bash
pip install -r requirements.txt
```

## Data Preparation

Ensure you have a raw SMILES file at `data/raw/smiles.csv` with columns `smiles` and `conductivity` (or `HOMO_LUMO_gap`).

## Execution Steps

### 1. Compute Descriptors
This step parses SMILES and computes graph-based descriptors.
```bash
python code/descriptors.py --output data/processed/descriptors.csv
```

### 2. Train Models and Save Results
This step trains Random Forest and Gradient Boosting models and saves initial results.
```bash
python code/save_model_results.py --data data/processed/descriptors.csv --output data/processed/model_results.json
```

### 3. Run Sensitivity Analysis (Optional but Recommended)
```bash
python code/run_sensitivity_analysis.py --data data/processed/descriptors.csv --output data/processed/sensitivity_analysis.json
```

### 4. Compute Feature Importance
```bash
python code/feature_importance.py --data data/processed/descriptors.csv --output data/processed/feature_importance.csv
```

### 5. Compute Correlations and Adjusted P-values
```bash
python code/correlation_analysis.py --data data/processed/descriptors.csv --output data/processed/correlation_results.json
```

### 6. Generate Analysis Summary
```bash
python code/run_analysis_summary.py
```

### 7. Generate Plots
```bash
python code/plot_top_features.py --output data/processed/corr_plot_top5.png
```

## Validation

Run the validation script to ensure all artifacts match schemas.
```bash
python code/validators.py --validate-all
```