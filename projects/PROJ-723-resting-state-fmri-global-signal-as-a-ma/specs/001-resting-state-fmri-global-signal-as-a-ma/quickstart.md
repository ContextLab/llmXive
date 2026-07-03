# Quickstart: Resting‑State fMRI Global Signal as a Marker of Mind‑Wandering

## Prerequisites
- Python 3.11+
- `pip`
- Access to internet (for downloading datasets)

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-723-resting-state-fmri-global-signal-as-a-ma
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `pandas`, `numpy`, `scikit-learn`, `nibabel`, `statsmodels` are installed.

## Running the Pipeline

### Step 1: Data Ingestion
Download the verified datasets and compute metrics.
```bash
python code/ingestion.py
```
*Output*: `data/processed/cleaned_data.csv` and `data/raw/` cache.

### Step 2: Primary Modeling
Run the ridge regression with nested CV, permutation testing (1,000), and reduced model comparison.
```bash
python code/modeling.py --data data/processed/cleaned_data.csv
```
*Output*: `data/results/primary_results.json`

### Step 3: Robustness Analysis
Run sensitivity checks (variance metric, alpha sweep).
```bash
python code/robustness.py --data data/processed/cleaned_data.csv
```
*Output*: `data/results/robustness_results.json`

### Step 4: Full Pipeline
Run all steps sequentially.
```bash
python code/main.py
```

## Testing

Run the test suite to verify data integrity and model logic.
```bash
pytest tests/ -v
```

## Troubleshooting
- **Memory Error**: If `ingestion.py` fails, reduce the `SAMPLE_SIZE` in `config.py`.
- **Dataset Mismatch**: If `ingestion.py` logs `FATAL: Dataset Mismatch`, the verified HCP URL does not contain the required time-series or global signal data. The study cannot proceed without raw data.
- **Missing MWQ**: Check `data/processed/cleaned_data.csv` for `NaN` in `mwq_score`.
- **High Collinearity**: If VIF > 5, the report will flag "High Collinearity" and interpret results as predictive gain rather than independent effect.