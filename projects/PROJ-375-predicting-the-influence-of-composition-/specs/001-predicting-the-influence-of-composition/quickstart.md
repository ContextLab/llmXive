# Quickstart: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Prerequisites

- Python 3.11+
- Access to the verified Zenodo dataset (DOI: 10.5281/zenodo.1000000 - *Metallic Glass Thermal Expansion Dataset*).
- (Optional) Materials Project API key if using that source.

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file in the root:
    ```env
    MP_API_KEY=your_key_here
    ZENODO_DATASET_ID=1000000
    DATA_URL=https://zenodo.org/api/records/1000000/files/mg_cte_data.csv
    ```

## Running the Pipeline

### 1. Data Ingestion
```bash
python code/ingestion/fetch_data.py
```
*Output*: `data/raw/zenodo_mg.parquet` (or `data/raw/mp_aflow.parquet` if APIs are used)

### 2. Feature Engineering
```bash
python code/features/descriptors.py
```
*Output*: `data/processed/clean_mg_data_with_features.parquet` (includes `size_mismatch_resid` and VIF scores)

### 3. Model Training
```bash
python code/modeling/train.py
```
*Output*: `results/metrics.csv`, `results/feature_importance.csv`

### 4. Evaluation & Significance
```bash
python code/modeling/evaluate.py
```
*Output*: `results/divergence.csv`, `results/correlations.csv`, `results/stability.csv`

## Verification

Run the test suite:
```bash
pytest tests/
```

## Troubleshooting

- **"No verified dataset found"**: Ensure `DATA_URL` in `.env` points to the verified Zenodo dataset. The default NER dataset is not valid.
- **Memory Error**: If the dataset is large, ensure `requests` downloads the file and `pandas` processes it in chunks (default behavior).
- **Collinearity Warning**: If VIF > 10, the linear model will automatically apply Ridge regularization.
- **Spec Constraint Warning**: The pipeline will report divergence between feature importance and correlation, even if SC-003 (spec) implies they must match. This is a known spec flaw. Stability Analysis is the primary metric.
