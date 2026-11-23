# Quickstart Guide

This guide provides instructions to run the full pipeline for predicting the glass-forming region of alloy systems.

## Prerequisites

- Python 3.11+
- All dependencies installed via `pip install -r requirements.txt`

## Running the Pipeline

Execute the following commands in order:

```bash
# 1. Data Ingestion
python code/ingestion.py

# 2. Feature Engineering
python code/features.py

# 3. Model Training
python code/train.py

# 4. Statistical Test
python code/statistical_test.py

# 5. SC-002 Gate
python code/t024c_gate.py

# 6. Sensitivity Analysis
python code/t031_sensitivity_analysis.py

# 7. Generate Report
python code/generate_report.py
```

## Output Files

- `data/processed/processed_alloys_raw.csv`: Raw processed data
- `data/processed/processed_alloys.csv`: Processed data with features
- `data/models/random_forest_model.pkl`: Trained Random Forest model
- `data/models/cv_metrics.json`: Cross-validation metrics
- `data/models/statistical_comparison.json`: Statistical test results
- `data/models/sensitivity_status.json`: Sensitivity analysis status
- `REPORT.md`: Final report

## Notes

- All scripts use `random_state=42` for reproducibility.
- The pipeline requires real data from the `matsci/glass-forming-ability` dataset.
- If any step fails, check the logs in `data/logs/`.
