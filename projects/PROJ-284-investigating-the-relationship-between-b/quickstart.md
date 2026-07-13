# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline is executed via `code/main.py` or specific script runners.

### Step 1: Download and Preprocess
```bash
python code/main.py --step download --subjects 50
python code/main.py --step preprocess --subjects 50
```

### Step 2: Extract Metrics
```bash
python code/main.py --step metrics --subjects 50
```

### Step 3: Analysis (T023a, T023b, T024)
This step performs PCA, merges metrics, and saves `full_metrics.csv`.
```bash
python code/main.py --step analyze --subjects 50
```

Alternatively, run the specific analysis script directly:
```bash
python code/analysis/generate_full_metrics.py
```

### Step 4: Visualization
```bash
python code/main.py --step viz --subjects 50
```

### Step 5: Report Generation
```bash
python code/main.py --step report --subjects 50
```

### Full Pipeline
```bash
python code/main.py --step all --subjects 50
```

## Output Files
- `data/processed/aggregated_metrics.csv`: Aggregated graph metrics per subject.
- `data/analysis/pca_loadings.csv`: PCA component loadings.
- `data/analysis/factor_scores.csv`: PCA factor scores per subject.
- `data/analysis/full_metrics.csv`: Merged dataset with raw metrics and PCA factors.
- `figures/`: Generated plots.
