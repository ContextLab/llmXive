# Quickstart Guide

## Overview
This guide provides step-by-step instructions to run the complete sleep quality prediction pipeline from raw data to final visualization.

## Prerequisites
- Python 3.10+
- pip
- Access to HCP data (or simulated data for testing)

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd PROJ-736-predicting-personal-sleep-quality-from-r
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline consists of several stages. Follow these steps in order:

### Step 1: Download and Prepare Data
```bash
python code/data/download_hcp.py
```
This will:
- Fetch HCP behavioral data
- Filter subjects with valid Sleep Scores
- Save filtered subject list

### Step 2: Preprocess fMRI Data
```bash
python code/data/preprocess.py
```
This will:
- Load CIFTI files for filtered subjects
- Apply Schaefer parcellation
- Perform nuisance regression and band-pass filtering
- Save preprocessed time series

### Step 3: Feature Engineering
```bash
python code/data/feature_engineering.py
```
This will:
- Compute pairwise correlations
- Apply Fisher-z transformation
- Extract upper-triangular vectors
- Save feature matrices

### Step 4: Train Predictive Model
```bash
python code/modeling/train.py
```
This will:
- Run nested cross-validation
- Tune ElasticNet hyperparameters
- Save predictions and model metrics

### Step 5: Evaluate Model
```bash
python code/modeling/evaluate.py
```
This will:
- Perform permutation tests on a subset
- Calculate bootstrap confidence intervals
- Run sensitivity analysis
- Save evaluation results

### Step 6: Interpret Model
```bash
python code/modeling/interpret.py
```
This will:
- Extract non-zero coefficients
- Map coefficients to brain edges
- Save interpretation results

### Step 7: Generate Visualization
```bash
python code/modeling/visualize.py
```
This will:
- Generate brain surface plot with top predictive connections
- Handle edge cases (<50 non-zero coefficients)
- Save plot to `data/results/brain_connectome_plot.png`

### Step 8: Finalize Report
```bash
python code/modeling/report_generator.py
```
This will:
- Compile all results into `ResultReport.json`
- Include metrics, p-values, CIs, and visualization paths

## Expected Outputs

After running the complete pipeline, you should have:

- `data/raw/behavioral/hcp1200_behavioral_data.csv` - Raw behavioral data
- `data/processed/` - Preprocessed time series and feature matrices
- `data/processed/predictions.npy` - Outer-fold predictions
- `data/results/ResultReport.json` - Comprehensive results report
- `data/results/brain_connectome_plot.png` - Brain connectivity visualization

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure all packages in `requirements.txt` are installed.
2. **Memory errors**: Reduce `subset_size` in config or use a smaller dataset.
3. **Time limits**: The pipeline enforces time budgets; adjust in config if needed.

### Logs

All pipeline stages log to `data/logs/pipeline_run.json`. Check this file for detailed error messages.

## Next Steps

- Review `ResultReport.json` for model performance metrics
- Examine `brain_connectome_plot.png` for key connectivity patterns
- Run tests in `tests/` to verify pipeline integrity