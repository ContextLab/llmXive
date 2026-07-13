# Quickstart Guide: Predicting Sleep Quality from fMRI

## Prerequisites
- Python 3.9+
- pip

## Setup
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution Steps
The pipeline consists of several stages. Run them in order:

### Step 1: Download and Filter Data (Task T007b)
This step downloads the HCP behavioral data and filters subjects based on Sleep Score and Framewise Displacement.
```bash
python code/data/download_hcp.py
```
*Output*: `data/raw/behavioral/hcp1200_behavioral_data.csv` and `data/processed/valid_subjects.json`

### Step 2: Preprocess Data (Task T008)
Preprocess the fMRI time series for the filtered subjects.
```bash
python code/data/preprocess.py
```

### Step 3: Feature Engineering (Task T009)
Compute connectivity matrices and vectorize them.
```bash
python code/data/feature_engineering.py
```

### Step 4: Train Model (Task T020)
Run the nested cross-validation training pipeline.
```bash
python code/modeling/train.py
```

### Step 5: Evaluate and Report (Task T022, T024, T026)
Run permutation tests, sensitivity analysis, and generate the final report.
```bash
python code/modeling/evaluate.py
python code/modeling/report_generator.py
```

## Verification
After running the full pipeline, check `data/results/ResultReport.json` for metrics.
Ensure `data/processed/predictions.npy` exists.