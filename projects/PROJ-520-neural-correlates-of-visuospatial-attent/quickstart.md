# Quickstart Guide

This guide provides the steps to run the full pipeline for the Neural Correlates of Visuospatial Attention project.

## Prerequisites

- Python 3.8+
- pip
- Required dependencies (see `requirements.txt`)

## Installation

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Set environment variables (optional):
 ```bash
 export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
 ```

## Execution

Run the pipeline steps in order. Each step corresponds to a task in `tasks.md`.

### Step 1: Download Data
```bash
python code/main.py --task download
```
This downloads the OpenNeuro dataset and validates BIDS structure.

### Step 2: Preprocess Data
```bash
python code/main.py --task preprocess
```
This filters, removes artifacts, and epochs the data.

### Step 3: Extract Features
```bash
python code/main.py --task features
```
This computes time-frequency features and extracts mean power for target electrodes.
**Note**: This step now also ensures `data/processed/features_matrix.csv` is written by calling the necessary logic.

### Step 4: Analyze Correlations (New)
```bash
python code/analyze_correlations.py
```
This computes correlation matrices, VIF, and saves `data/processed/feature_metadata.json`.
This step is required for T024 and T029.

### Step 5: Classification (Optional for T024)
```bash
python code/main.py --task classify
```

## Output Artifacts

After successful execution, the following files should exist:
- `data/processed/epochs_cleaned.fif`
- `data/processed/tf_power.npy`
- `data/processed/features_matrix.csv`
- `data/processed/feature_metadata.json`
- `results.json`

## Troubleshooting

- If you encounter `ImportError`, ensure `PYTHONPATH` is set correctly.
- If data download fails, check your internet connection and OpenNeuro availability.
- If `features_matrix.csv` is missing, ensure `code/analyze_correlations.py` or `code/save_features.py` is run.
- If `feature_metadata.json` is missing, run `python code/analyze_correlations.py`.