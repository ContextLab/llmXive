# Quickstart Guide

This guide walks you through running the full sleep quality prediction pipeline.

## Prerequisites

- Python 3.9+
- pip and virtual environment

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline consists of several stages. Run them in order:

### 1. Download HCP Data
```bash
python code/data/download_hcp.py
```
This downloads and processes the HCP 1200 behavioral data.
Output: `data/raw/behavioral/hcp1200_behavioral_data.csv`

### 2. Run Main Pipeline
```bash
python code/main.py
```
This orchestrates the full pipeline:
- Downloads raw data
- Preprocesses fMRI data
- Extracts connectivity features
- Trains the prediction model
- Saves predictions to `data/processed/predictions.npy`

### 3. Bootstrap Resampling (T023)
```bash
python code/modeling/evaluate.py
```
This performs bootstrap resampling on the predictions to compute R² confidence intervals.
Output: `data/results/bootstrap_ci.json`

### 4. Generate Final Report
```bash
python code/modeling/finalize_report.py
```
This compiles all results into `data/results/ResultReport.json`.

## Expected Outputs

After running the full pipeline, you should have:
- `data/raw/behavioral/hcp1200_behavioral_data.csv` - Behavioral data
- `data/processed/predictions.npy` - Model predictions
- `data/results/bootstrap_ci.json` - Bootstrap confidence intervals
- `data/results/ResultReport.json` - Comprehensive results report

## Troubleshooting

- If you encounter missing module errors, ensure you've installed all dependencies from `requirements.txt`.
- If the pipeline fails during data download, check your internet connection and HCP data access permissions.
- For memory issues, consider reducing the dataset size or increasing available RAM.