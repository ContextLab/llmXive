# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r code/requirements.txt
```

## Usage

### 1. Download Data
```bash
python code/data/download_qm9.py
```

### 2. Preprocess Descriptors
```bash
python code/data/preprocess_2d.py
```

### 3. Train Model
```bash
python code/models/train_lightgbm.py
```

### 4. Evaluate Model
```bash
python code/models/evaluate.py
```

### 5. Compute Cluster-Aware SHAP (T032b)
```bash
python code/models/interpret.py \
 --model data/processed/model.pkl \
 --data data/processed/descriptors.parquet \
 --clusters data/processed/cluster_map.csv \
 --output data/processed/analysis
```

### 6. Generate Stability Report
```bash
python code/models/generate_stability_report.py
```

## Data Sources
- QM9: Loaded via `datasets` package from `jablonkagroup/qm9`
- Output files are stored in `data/processed/` and `data/processed/analysis/`
