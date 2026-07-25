# Quickstart: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Prerequisites

- Python 3.11+
- `pip`
- Internet access (for downloading MatsSci-Glass data)

## Installation

1.  **Clone the repository** (if not already done).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will contain `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `mendeleev`.*

## Running the Pipeline

The pipeline is executed in three sequential steps:

### 1. Data Ingestion & Feature Engineering
Downloads the MatsSci-Glass dataset, cleans it, and computes thermodynamic descriptors.
```bash
python code/ingestion.py
python code/features.py
```
*Output*: `data/processed/featurized_alloys.csv` (contains ≥500 rows if successful).

### 2. Model Training & Cross-Validation
Trains the Random Forest model and performs 5-fold CV.
```bash
python code/train.py
```
*Output*: `data/outputs/model_metrics.json`, `data/outputs/trained_model.pkl`.

### 3. Analysis & Sensitivity
Performs permutation importance and threshold sensitivity analysis.
```bash
python code/analyze.py
```
*Output*: `data/outputs/sensitivity_report.json`, `data/outputs/feature_importance.csv`.

## Validation

To verify the pipeline:
1.  Ensure `data/processed/featurized_alloys.csv` has at least 500 rows.
2.  Check `data/outputs/model_metrics.json` for `p_value_null` < 0.05.
3.  Run `pytest tests/` to verify unit tests for feature calculations.

## Troubleshooting

- **Data Availability Error**: If the script fails with "Insufficient data", the verified MatsSci-Glass URL may not contain the required `critical_cooling_rate` column. Check the raw data file manually.
- **Memory Error**: If running out of RAM, ensure no other heavy processes are running. The pipeline is optimized for moderate RAM requirements.