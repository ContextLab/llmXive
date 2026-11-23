# Quickstart Guide

## Prerequisites
- Python 3.10+
- pip

## Setup
1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Set environment variables:
 ```bash
 export MP_API_KEY="your_api_key_here"
 ```

## Run the Pipeline
Execute the full pipeline in order:

1. **Download raw data**:
 ```bash
 python code/cli/download_cli.py --extract
 ```

2. **Clean and validate data**:
 ```bash
 python code/data/clean.py
 ```

3. **Train and evaluate models**:
 ```bash
 python code/modeling.py
 ```

4. **Run analysis (Permutation Importance)**:
 ```bash
 python code/analysis.py
 ```

5. **Generate final report**:
 ```bash
 python code/main.py
 ```

## Expected Outputs
- `data/processed/alloys_clean.parquet` - Cleaned dataset
- `models/rf_model.pkl` - Trained Random Forest model
- `results/model_metrics.json` - Model performance metrics
- `results/feature_importance.json` - Feature importance results
- `results/final_report.md` - Final analysis report

## Validation
Run tests:
```bash
pytest --cov=code
```