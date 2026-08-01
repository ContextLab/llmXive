# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Preparation
1. Run the download script to fetch real data (T043a):
 ```bash
 python code/data/download.py --url <NIST_URL> --output-dir data/raw
 ```
 *Note: Replace <NIST_URL> with the actual NIST data URL.*

2. Run the preprocessing pipeline (T015, T016):
 ```bash
 python code/data/preprocess.py --data-dir data/raw --target langmuir_capacity
 ```
 This will generate `data/processed/outliers.csv` and the cleaned dataset.

## Model Training
1. Run the training pipeline (T020-T022):
 ```bash
 python code/main.py --data-dir data/processed --task train_model --target langmuir_capacity
 ```

## Evaluation & SHAP
1. Run evaluation and SHAP analysis:
 ```bash
 python code/main.py --data-dir data/processed --task shap_analysis
 ```

## Validation
1. Validate the quickstart run:
 ```bash
 python code/scripts/validate_quickstart.py
 ```

## Notes
- Ensure `data/raw` contains the downloaded CSV before running preprocess.
- The outlier detection (T016) runs automatically during preprocessing.
- All data must be real; synthetic data is strictly prohibited.