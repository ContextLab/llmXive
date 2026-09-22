# Quickstart Guide for Glass-Forming Region Prediction Pipeline

## Prerequisites

- Python 3.9+
- pip
- git

## Installation

1. Clone the repository:
 ```bash
 git clone <repo-url>
 cd PROJ-510-predicting-the-glass-forming-region-of-a
 ```

2. Create and activate virtual environment:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

Execute the pipeline in the following order:

```bash
# 1. Data Ingestion
python code/ingestion.py

# 2. Feature Engineering
python code/features.py

# 3. Model Training
python code/train.py

# 4. Analysis
python code/analyze.py

# 5. Generate Report
python code/generate_report.py

# 6. Validation
python code/validate_schemas.py
python code/audit_data_source.py
python code/check_sc002.py
python code/check_sc003.py
```

## Output Artifacts

After successful execution, the following artifacts will be generated:

- `data/processed/processed_alloys_raw.csv` - Raw processed data
- `data/processed/processed_alloys.csv` - Final engineered dataset
- `data/models/random_forest_model.pkl` - Trained model
- `data/models/cv_metrics.json` - Cross-validation metrics
- `data/models/statistical_comparison.json` - Statistical test results
- `data/models/sensitivity_status.json` - Sensitivity analysis results
- `REPORT.md` - Final research report

## Notes

- All random operations use `random_state=42` for reproducibility.
- The pipeline uses the `matsci/glass-forming-ability` dataset from Hugging Face.
- Ensure you have internet access for dataset download.
- The pipeline is designed to run on CPU; no GPU required.