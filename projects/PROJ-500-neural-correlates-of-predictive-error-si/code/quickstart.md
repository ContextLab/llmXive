# Quickstart Guide

This guide provides the commands to run the full pipeline end-to-end.
Ensure you have installed dependencies via `pip install -r requirements.txt`.

## Prerequisites
- Python 3.11+
- Data directory structure created (run `python code/setup_project.py` if not done)

## Execution Steps

### 1. Data Ingestion (Optional - if raw data not present)
```bash
python code/src/data/ingest.py
```

### 2. Preprocessing
```bash
python code/src/data/preprocess.py
```

### 3. Alignment (Behavioral Binning & Lagged Alignment)
```bash
python code/src/data/align.py
```

### 4. Finalization (T024 - Merge & Write Aligned Data)
```bash
python code/src/data/finalize.py
```

### 5. Statistical Modeling
```bash
python code/src/analysis/model.py
```

## Output Artifacts
Upon successful completion, the following files will be generated in `data/`:
- `validation_report.json`
- `excluded_subjects.csv`
- `interim_lagged_mmns.csv`
- `accuracy_blocks.csv`
- `aligned_data.csv` (Final Dataset)
- `model_output.json`
