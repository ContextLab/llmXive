# Quickstart: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## Prerequisites
*   Python 3.11+
*   `git`
*   Access to Hugging Face (for dataset download, no token required for public datasets)

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-145-evaluating-the-predictive-power-of-machi
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    Ensure `pymatgen`, `scikit-learn`, and `pandas` are installed:
    ```bash
    python -c "import pymatgen; import sklearn; print('Dependencies OK')"
    ```

## Running the Pipeline

The pipeline is executed via a single entry point script that orchestrates data ingestion, training, and evaluation.

```bash
python code/run_pipeline.py
```

### Step-by-Step Breakdown (Manual Execution)

If you wish to run stages individually:

1.  **Ingest Data** (FR-001, FR-002)
    ```bash
    python code/data_ingestion.py
    # Outputs: data/processed/heas_train.csv, holdout_known.csv, true_novel.csv
    ```

2.  **Feature Engineering** (FR-003)
    ```bash
    python code/feature_engineering.py
    # Outputs: data/processed/heas_train_features.csv
    ```

3.  **Train Models** (FR-004)
    ```bash
    python code/model_training.py
    # Outputs: models/rf_model.pkl, models/gb_model.pkl
    ```

4.  **Evaluate** (FR-005-FR-008)
    ```bash
    python code/evaluation.py
    # Outputs: data/results/report.csv
    ```

## Expected Outputs
*   `data/processed/heas_train.csv`: Filtered training data.
*   `data/processed/holdout_known.csv`: Known compositions excluded from training.
*   `data/processed/true_novel.csv`: Novel candidates.
*   `data/processed/heas_train_features.csv`: Feature-engineered training data.
*   `data/results/report.csv`: Final metrics and top novel candidates.

## Troubleshooting
*   **API Rate Limits**: The script implements exponential backoff. If it fails after 3 retries, it logs "partial failure" and continues.
*   **Memory Errors**: If `pandas` crashes due to memory, enable `streaming=True` in `data_ingestion.py` (requires code modification).
*   **Descriptor Errors**: If `pymatgen` fails to find an element, check the elemental list in `config.py`.
