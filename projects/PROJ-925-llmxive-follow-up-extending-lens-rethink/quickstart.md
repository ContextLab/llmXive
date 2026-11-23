# Quickstart Guide: llmXive Follow-up Project

## Prerequisites
- Python 3.9+
- pip
- Git

## Setup
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Initialize project structure (if not done):
 ```bash
 python code/setup_project.py
 ```

## Execution Pipeline
Run the following commands in order to execute the full pipeline.
Ensure you have enough disk space for the `pick-a-pic` dataset (~7GB+).

### Phase 1: Data Download
```bash
python code/data/download.py
```
*Output*: `data/raw/pick-a-pic.parquet`

### Phase 2: Feature Extraction
```bash
python code/data/features.py
```
*Output*: `data/processed/features.csv`, `data/logs/exclusions.log`, `data/processed/exclusion_summary.json`

### Phase 3: Deviation Calculation
```bash
python code/data/preprocess.py
```
*Output*: `data/processed/deviation.csv`

### Phase 4: Train/Validation Split (T018c)
```bash
python code/data/split_features.py
```
*Output*: `data/processed/features_train.csv`, `data/processed/features_held_out.csv`

### Phase 5: Model Training & Significance
```bash
python code/data/train.py
```
*Output*: `results/significance.json`, `results/stability_metrics.json`

## Validation
Run constitution checks:
```bash
pytest code/tests/test_constitution.py
```

Run specific task tests:
```bash
pytest code/tests/test_features.py
pytest code/tests/test_preprocess.py
pytest code/tests/test_train.py
```

## Note on Data
The pipeline requires the `pick-a-pic` dataset. If the download fails, ensure you have internet access and sufficient disk space. The script will fail loudly if the dataset cannot be fetched.