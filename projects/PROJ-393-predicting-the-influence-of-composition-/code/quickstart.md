# Quickstart Guide for Heusler Alloy Hysteresis Prediction

## Prerequisites
- Python 3.11+
- Virtual environment activated

## Installation
```bash
pip install -r code/requirements.txt
```

## Running the Pipeline
Execute the full pipeline end-to-end:
```bash
cd code
python main.py
```

## Expected Outputs
- `data/processed/alloys_raw.csv`
- `data/processed/alloys_features.csv`
- `data/processed/model_metrics.json`
- `docs/reports/final_report.md`

## Manual Data Curation
If automated fetchers fail, populate `data/raw/manual_curated.csv` using the template `data/raw/manual_curated_template.csv`.