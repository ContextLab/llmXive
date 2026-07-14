# Quickstart Guide

This guide validates the pipeline execution and artifact generation.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`

## Execution Steps

1. **Generate Mock Data** (if real data is not available or for CI):
 ```bash
 python code/scripts/generate_mock_data.py
 ```
 This creates:
 - `data/raw/genomic_vcf.json`
 - `data/raw/env_data.json`
 - `data/raw/compound_data.json`

2. **Run Validation Pipeline**:
 ```bash
 python code/data/validation.py
 ```
 This merges datasets and produces `data/processed/merged.csv`.

3. **Run Preprocessing Pipeline** (Imputation, Filtering, VIF):
 ```bash
 python code/data/preprocessing.py
 ```
 This produces:
 - `data/processed/filtered.csv`
 - `data/processed/features_vif.csv`

4. **Run Model Training**:
 ```bash
 python code/models/training.py
 ```

5. **Run Evaluation**:
 ```bash
 python code/models/evaluation.py
 ```

6. **Run Full Pipeline**:
 ```bash
 python code/main.py
 ```

## Verification

Ensure the following files exist after execution:
- `data/raw/genomic_vcf.json`
- `data/raw/env_data.json`
- `data/raw/compound_data.json`
- `data/processed/filtered.csv`
- `data/processed/features_vif.csv`
- `state/PROJ-475-predicting-plant-defense-compound-produc.yaml`