# Quickstart: Machine Learning Prediction of Crack Propagation Rates in Metals

## Prerequisites

- Python 3.11+
- `pip` and `venv`
- Git

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/001-crack-propagation-ml
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    Ensure `scikit-learn`, `xgboost`, `optuna`, and `ruptures` are installed and compatible with CPU execution.
    ```bash
    python -c "import xgboost; import ruptures; print('OK')"
    ```

## Running the Pipeline

The pipeline is executed via the `main.py` entry point in `code/`.

1.  **Download and Validate Data**
    ```bash
    python code/main.py --step download
    ```
    *This step fetches the dataset from the verified HuggingFace URL, calculates the checksum, and **verifies the presence of required columns** ($da/dN$, $\Delta K$, composition, heat treatment). If validation fails, the script halts with a clear error message.*

2.  **Preprocess Data**
    ```bash
    python code/main.py --step preprocess
    ```
    *This step handles missing values, log-transforms, and encoding. Output saved to `data/processed/`.*

3.  **Train Baseline Model**
    ```bash
    python code/main.py --step baseline
    ```
    *Trains the Paris Law linear regression (stratified by alloy family) and outputs $R^2$ and PDP.*

4.  **Train Augmented Models**
    ```bash
    python code/main.py --step augmented
    ```
    *Runs Optuna tuning and trains RF/XGBoost models. Outputs $\Delta R^2$ and feature importance. Uses Permutation Test for significance.*

5.  **Regime Analysis**
    ```bash
    python code/main.py --step regimes
    ```
    *Identifies Low/Mid/High regimes using change-point detection and generates sensitivity reports.*

## Reproducibility

To ensure reproducibility on a fresh runner:
```bash
# Reset random seeds in config.py if needed
# Re-run the full pipeline
python code/main.py --step full
```
All outputs will be deterministic due to pinned seeds in `code/config.py`.

## Validation

Run the test suite to verify data integrity and model logic:
```bash
pytest tests/
```