# Quickstart: Predicting the Glass Forming Region

## Prerequisites

- Python 3.11+
- `pip`
- Access to Zenodo/Figshare (for dataset download)

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-510-predicting-the-glass-forming-region-of-a
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    # requirements.txt includes: pandas, scikit-learn, mendeleev, datasets, pyyaml, pytest, scipy
    ```

## Running the Pipeline

The pipeline is executed in stages. Each stage produces artifacts and logs.

### Step 1: Data Ingestion & Feature Engineering
Downloads experimental CCR data, filters for ternary alloys, computes descriptors.
```bash
python code/ingestion.py
python code/features.py
```
- **Outputs**:
  - `data/processed/processed_alloys.csv`
  - `data/logs/exclusion_log.txt`
  - `data/logs/ingestion_hash.txt` (SHA-256 of processed CSV)
- **Validation**: Check `data/logs/exclusion_log.txt` for any "Empty dataset" errors.

### Step 2: Model Training & Cross-Validation
Trains Random Forest, performs 5-fold CV, compares to dummy baseline (Two-sided t-test).
```bash
python code/train.py
```
- **Outputs**:
  - `data/models/random_forest_model.pkl`
  - `data/models/cv_metrics.json`
- **Validation**: Ensure `cv_metrics.json` contains `mean_rmse`, `p_value`, `oob_score`.

### Step 3: Analysis & Sensitivity
Permutation importance, threshold sweep (50/100/150 K/s), collinearity check.
```bash
python code/analyze.py
```
- **Outputs**:
  - `data/models/sensitivity_report.json`
  - `data/models/feature_importance_ranking.csv`

### Step 4: Validation & Reporting
Validates ALL 4 schemas and generates the final report.
```bash
python code/validate_schemas.py
# If all pass, generate REPORT.md (template-driven)
python code/generate_report.py
```

## Testing

Run unit tests to verify feature calculations and error handling:
```bash
pytest tests/unit/ -v
```
- **Key Tests**:
  - `test_mixing_enthalpy`: Verifies thermodynamic formula.
  - `test_size_mismatch`: Verifies atomic size calculation.
  - `test_empty_dataset`: Verifies graceful failure on missing data.

## Troubleshooting

- **"Dataset is empty"**: The experimental source may lack `critical_cooling_rate`. Check `data/logs/fetch_error.log`.
- **"Data Insufficiency"**: If N < 500 after both sources, the pipeline halts.
- **Schema Validation Failed**: Ensure `processed_alloys.csv` matches `contracts/dataset.schema.yaml`.
- **Memory Error**: Unlikely for N=500, but reduce `n_estimators` in `train.py` if needed.
- **Associational Framing**: The `REPORT.md` template enforces a disclaimer. Do not edit the template to remove it.