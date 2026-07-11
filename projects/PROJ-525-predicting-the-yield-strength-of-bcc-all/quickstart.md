# Quick Start Guide

## Prerequisites
- Python 3.11+
- `pip`

## Installation
```bash
pip install -r requirements.txt
```

## Running the Pipeline

### Step 1: Data Ingestion (US1)
Downloads the MPEA database and filters for BCC alloys.
```bash
python code/data_ingestion.py
```
Output: `data/processed/bcc_filtered.csv`

### Step 2: Feature Engineering (US2)
Calculates compositional descriptors and ILR transformations.
```bash
python code/feature_engineering.py
```
Output: `data/processed/features_engineered.csv`

### Step 3: Modeling (US3)
Trains models and generates comparison reports.
```bash
python code/modeling.py
```
Output: `reports/model_comparison_report.json`

## Validation
Run tests to verify the pipeline:
```bash
python -m pytest tests/ -v
```
