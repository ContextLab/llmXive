# Quickstart: Predicting Solubility in Mixed Solvents

## Prerequisites

*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI) or local environment with ≥8 GB RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-142-predicting-solubility-in-mixed-solvents-
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Preparation

The pipeline automatically downloads data from verified sources on first run.

1.  **Run the ingestion script**:
    ```bash
    python code/01_data_ingestion.py
    ```
    *   Downloads MoleculeNet and EPA CSVs to `data/raw/`.
    *   Filters for MW < 500 and valid mixtures.
    *   Outputs `data/processed/cleaned_solubility.csv`.

2.  **Verify data**:
    Check `data/processed/cleaned_solubility.csv` for expected columns and row counts.

## Feature Engineering

1.  **Run the feature engineering script**:
    ```bash
    python code/02_feature_engineering.py
    ```
    *   Computes RDKit descriptors.
    *   Generates composition-weighted solvent properties.
    *   Creates interaction terms.
    *   Outputs `data/processed/features_enriched.csv`.

## Model Training & Evaluation

1.  **Run the training script**:
    ```bash
    python code/03_model_training.py
    ```
    *   Trains XGBoost, Random Forest, and Abraham baseline.
    *   Performs 5-fold CV.
    *   Saves models to `artifacts/models/`.

2.  **Run the evaluation script**:
    ```bash
    python code/04_evaluation.py
    ```
    *   Computes metrics (RMSE, R²).
    *   Runs paired t-test.
    *   Generates SHAP plots and sensitivity analysis.
    *   Outputs reports to `artifacts/reports/`.

## Testing

Run the test suite to verify contract compliance:

```bash
pytest tests/ -v
```

## CI/CD

Push to the feature branch to trigger GitHub Actions:
*   **Job**: `train-model`
*   **Limits**: 2 CPU, 7 GB RAM, 6 hours.
*   **Outcome**: If successful, artifacts and reports are uploaded as build artifacts.