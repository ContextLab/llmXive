# Quickstart Guide for Predicting Perovskite Stability Pipeline

## Prerequisites
- Python 3.11+
- Required packages listed in `code/requirements.txt`

## Setup
1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
2. Configure environment variables in `.env` (see `code/config.yaml` for keys).

## Running the Pipeline

### Step 1: Initialize State
```bash
python -m code.utils.state_manager update data/raw/test_dummy.csv
```
This creates `state/project_state.yaml` and records the hash of the dummy file.

### Step 2: Data Ingestion
```bash
python code/data_ingestion.py
```
Fetches NREL and Materials Project data, validates, and merges into `data/raw/perovskites_merged.csv`.

### Step 3: Metadata & Uncertainty
```bash
python code/data_ingestion_metadata.py
python code/propagate_uncertainty.py
```
Extracts instrumentation metadata and computes uncertainty weights.

### Step 4: Feature Engineering
```bash
python code/feature_engineering.py
```
Computes compositional descriptors (atomic fractions, weighted properties).

### Step 5: VIF Diagnostics & Filtering
```bash
python code/vif_diagnostic.py
python code/filter_vif_features.py
python code/filter_descriptors.py
```
Identifies collinear features and filters the dataset.

### Step 6: Model Training
```bash
python code/model_training.py
```
Trains Random Forest, Gradient Boosting, and Elastic Net models with grid search.

### Step 7: Validation & Reporting
```bash
python code/validation.py
```
Performs external validation and generates final reports.

## Verification
Check `state/project_state.yaml` to ensure all artifacts have been hashed.
Review `data/processed/validation_report.md` for final metrics.