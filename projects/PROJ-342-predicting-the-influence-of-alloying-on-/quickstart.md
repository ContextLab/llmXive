# Quickstart Guide

## Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline
Execute the full pipeline end-to-end:
```bash
python code/ingest.py
python code/descriptors.py
python code/train.py
python code/analyze.py
python code/report.py
```

## Verification
Verify artifacts after running:
```bash
python code/verify_artifacts.py
```

## Configuration
- Set environment variables in `.env` for Zenodo DOIs and resource limits.
- Modify `config.yaml` for hyperparameters and limits.

## Output Artifacts
- `data/processed/cleaned_mg.csv`: Cleaned dataset.
- `data/processed/descriptors.csv`: Computed descriptors.
- `artifacts/models/best_model.pkl`: Trained model.
- `artifacts/metrics/metrics.json`: Performance metrics.
- `artifacts/reports/final_report.md`: Final analysis report.
