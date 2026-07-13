# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## Running the Pipeline
1. **Download Data**:
 ```bash
 python code/01_download.py
 ```
 This fetches the MeLiDC dataset from HuggingFace and saves it to `data/raw/`.

2. **Preprocess Data**:
 ```bash
 python code/02_preprocess.py
 ```
 This filters for BCC Carbon, computes descriptors, and saves `data/processed/dataset_cleaned.csv`.

3. **Train Models**:
 ```bash
 python code/03_train.py
 ```
 This trains RF, XGBoost, and Elastic Net models, performs grid search, and saves results to `data/outputs/`.

4. **Evaluate**:
 ```bash
 python code/04_evaluate.py
 ```
 This computes SHAP values, generates plots, and outputs `feature_importance.json` and `variance_partition.csv`.

## Tests
Run tests with:
```bash
pytest tests/
```
