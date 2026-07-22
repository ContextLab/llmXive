# Quickstart Guide: Predicting Molecular Interactions in Ionic Liquids

## Prerequisites
- Python 3.9+
- Virtual environment with dependencies installed (`code/requirements.txt`)

## Setup
1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r code/requirements.txt
 ```

2. Run Data Ingestion (T012a, T013c, T016, T017e):
 ```bash
 python code/data_ingestion.py
 ```
 This will:
 - Download SPICE dataset to `data/raw/spice.parquet`
 - Extract structures to `data/raw/il_structures.json`
 - Engineer features and save to `data/processed/unified_dataset.parquet`

3. Run Model Training (T021a, T022, T026):
 ```bash
 python code/model_training.py
 ```
 This will:
 - Split data and save to `data/processed/train.parquet`, `val.parquet`, `test.parquet`
 - Train models and save to `models/`

4. Run Analysis (T030, T038):
 ```bash
 python code/analysis.py
 ```
 This will:
 - Run ANOVA and Tukey HSD
 - Validate against DFT (if available)
 - Log p-values, effect sizes, and MAE
 - Save reports to `contracts/` and `analysis/`

## Expected Outputs
- `data/raw/spice.parquet`
- `data/raw/il_structures.json`
- `data/processed/unified_dataset.parquet`
- `data/processed/train.parquet`
- `models/energy_models_electrostatic.pkl` (and others)
- `analysis/anova_results.json`
- `contracts/validation_report.json`