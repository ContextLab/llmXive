# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Run Pipeline

### 1. Load and Validate Data
```bash
python code/run_descriptor_pipeline.py --input data/raw/smiles.csv --output data/processed/descriptors_augmented.csv
```

### 2. Train Models (Initial)
```bash
python code/model_training.py --data data/processed/descriptors_augmented.csv --output data/processed/model_results.json
```

### 3. Run VIF Loop with Hückel Feature (T064)
```bash
python code/run_huckel_vif_loop.py --data data/processed/descriptors_augmented.csv --output data/processed/huckel_impact_report.json
```

### 4. Generate Feature Importance and Analysis Summary
```bash
python code/save_analysis_outputs.py --data data/processed/descriptors_augmented.csv --target conductivity
```

### 5. Validate Outputs
```bash
python code/validators.py --validate data/processed/descriptors_augmented.csv --schema contracts/descriptor_schema.yaml
python code/validators.py --validate data/processed/huckel_impact_report.json --schema contracts/model_results_schema.yaml
```
