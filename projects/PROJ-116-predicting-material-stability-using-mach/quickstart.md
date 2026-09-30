# Quick Start Guide

## Prerequisites
- Python 3.11+
- pip

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

### Step 1: Download Data
```bash
python code/download_data.py
```
This fetches OQMD data and filters for Li-rich rock-salt structures.

### Step 2: Feature Engineering
```bash
python code/feature_engineering.py
```
Computes Magpie features and (optionally) local coordination features.

### Step 3: Train Baseline Model
```bash
python code/train_baseline.py
```
Trains a Gradient Boosting model on compositional features.

### Step 4: Train Augmented Model
```bash
python code/train_augmented.py
```
Trains a model with additional local coordination features.

### Step 5: Evaluate Models
```bash
python code/evaluate.py
```
Generates predictions and comparison metrics.

## Output Files

- `data/raw/oqmd_filtered.csv`: Filtered dataset
- `data/processed/baseline_features.parquet`: Compositional features
- `data/processed/augmented_features.parquet`: Combined features
- `data/models/baseline_model.pkl`: Baseline model
- `data/models/augmented_model.pkl`: Augmented model
- `outputs/baseline_results.csv`: Baseline predictions
- `outputs/comparison_metrics.json`: Model comparison
- `outputs/figures/feature_importance.png`: Feature importance plot

## Logging

All logs are stored in `outputs/logs/`.