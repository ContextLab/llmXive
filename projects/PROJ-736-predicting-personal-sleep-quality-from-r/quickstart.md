# Quickstart Guide: Predicting Personal Sleep Quality from Resting-State fMRI

## Prerequisites
- Python 3.8+
- pip
- Access to HCP data (or pre-downloaded files)

## Setup
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Run the data pipeline (T005 + T007b + T008 + T009 + T014):
 ```bash
 # Step 1: Download raw behavioral data (if not present)
 python code/data/download_hcp.py

 # Step 2: Run the full pipeline orchestration
 python code/main.py
 ```

## Expected Outputs
- `data/raw/behavioral/hcp1200_behavioral_data.csv`: Raw behavioral data
- `data/processed/valid_subject_ids.json`: List of subjects passing filters
- `data/processed/predictions.npy`: Model predictions
- `data/results/ResultReport.json`: Final results report

## Troubleshooting
- If `ModuleNotFoundError: No module named 'requests'`, run `pip install requests`.
- If behavioral file is missing, ensure you have credentials for HCP or place the file manually at `data/raw/behavioral/hcp1200_behavioral_data.csv`.