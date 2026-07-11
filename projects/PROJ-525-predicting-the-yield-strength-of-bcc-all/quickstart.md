# Quick Start Guide

## Prerequisites
- Python 3.11+
- Installed dependencies (`pip install -r requirements.txt`)

## Step 1: Data Preparation
Place the raw MPEA database file at `data/raw/mpea_raw.csv`.
Ensure the file contains columns: `crystal_structure`, `yield_strength`, and elemental composition columns.

## Step 2: Run Data Ingestion (User Story 1)
Execute the download and filtering script:
```bash
python code/01_download.py
```
This will produce `data/processed/bcc_filtered.csv`.

## Step 3: Run Feature Engineering (User Story 2)
Once data is filtered, run:
```bash
python code/02_engineer.py
```

## Step 4: Run Model Training (User Story 3)
```bash
python code/03_train.py
```

## Validation
To validate the project structure and dependencies:
```bash
python code/config.py --validate
```