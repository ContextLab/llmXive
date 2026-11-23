# Quickstart Guide

This guide explains how to run the full pipeline from data download to final plots.

## Prerequisites

- Python 3.10+
- Install dependencies: `pip install -r code/requirements.txt`

## Execution

Run the full pipeline with a single command:

```bash
python code/main.py
```

Alternatively, run individual steps:

```bash
# 1. Ingest Data
python code/ingestion.py

# 2. Preprocess Data
python code/preprocessing.py

# 3. Model & Analyze
python code/modeling.py

# 4. Visualize
python code/viz.py

# 5. Verify Reproducibility
python code/verify_reproducibility.py
```

## Outputs

- `data/processed/merged_sample.parquet`: Cleaned and sampled dataset.
- `data/state/model_results.json`: Statistical model results.
- `data/processed/figures/`: Generated plots.
