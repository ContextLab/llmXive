# Quick Start Guide

## 1. Setup Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Initialize Project Structure
```bash
python code/setup_data_structure.py
```
This creates the necessary `data/`, `state/`, and `reports/` directories.

## 3. Run Pipeline
1. **Ingest Data**:
 ```bash
 python code/01_data_ingestion.py
 ```
 Fetches ESOL dataset from MoleculeNet, validates schema, and saves to `data/processed/raw_esol.csv`.

2. **Compute TDA Features**:
 ```bash
 python code/02_tda_computation.py
 ```
 Generates `data/processed/tda_features.csv` and `data/processed/traditional_descriptors.csv`.

3. **Train Models**:
 ```bash
 python code/04_model_training.py
 ```
 Trains Linear Regression and Random Forest models, outputs `reports/metrics/model_performance.json`.

## 4. Validation
Run tests to ensure integrity:
```bash
pytest tests/ -v
```