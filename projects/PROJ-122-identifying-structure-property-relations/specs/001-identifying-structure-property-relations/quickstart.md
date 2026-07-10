# Quickstart: Identifying Structure-Property Relationships in Polymer Blends

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the Polymer Database, NIST, and Materials Project APIs (or pre-downloaded data in `data/raw/`).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-122-identifying-structure-property-relations
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Preparation

1.  **Fetch Data**:
    Run the ingestion script. It will attempt to fetch from APIs. If APIs are unreachable, it will look for `data/raw/polymer_db.csv`, `data/raw/nist.json`, etc.
    ```bash
    python code/01_ingest.py
    ```
    *Output*: `data/processed/harmonized.csv`

2.  **Verify Data**:
    Check the log for excluded rows (invalid SMILES, bad composition).
    ```bash
    cat logs/ingest.log
    ```

## Feature Engineering

Generate molecular descriptors and interaction features:
```bash
python code/02_features.py
```
*Output*: `data/processed/features.parquet`

## Model Training & Validation

Train models, perform VIF sensitivity analysis, and run stability checks:
```bash
python code/03_train.py
```
*Output*: `data/artifacts/models/`, `data/artifacts/shap_values.csv`, `data/artifacts/stability_report.json`

## Reporting

Generate the final summary table, SHAP plots, and stability charts:
```bash
python code/04_report.py
```
*Output*: `data/artifacts/final_report.md`, `data/artifacts/plots/`

## Testing

Run unit and integration tests:
```bash
pytest tests/
```

## Troubleshooting

*   **Data Insufficiency**: If `N < 100`, the pipeline halts with `DataInsufficiencyError`.
*   **API Rate Limits**: The script implements exponential backoff. If it fails after 5 retries, check your API key or network.
*   **Memory Error**: If running out of RAM, reduce the `n_estimators` in `code/03_train.py` or sample the dataset in `code/01_ingest.py`.
