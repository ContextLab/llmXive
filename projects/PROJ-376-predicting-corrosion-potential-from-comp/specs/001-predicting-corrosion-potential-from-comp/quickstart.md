# Quickstart: Predicting Corrosion Potential from Composition and Environment

## Prerequisites

*   Python 3.11+
*   pip / virtualenv
*   Access to GitHub Actions (for CI execution) or a local environment with substantial RAM.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-376-predicting-corrosion-potential-from-comp
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Configuration

1.  **Set Random Seeds**:
    Create `code/config/seeds.yaml` (if not present):
    ```yaml
    random_seed: 42
    numpy_seed: 42
    tensorflow_seed: 42
    ```

2.  **Define Paths**:
    Create `code/config/paths.yaml`:
    ```yaml
    raw_data_dir: "data/raw"
    processed_data_dir: "data/processed"
    logs_dir: "data/logs"
    contracts_dir: "contracts"
    ```

## Running the Pipeline

The pipeline is executed via the CLI script. It handles download, validation, training, and evaluation.

### Step 1: Data Ingestion & Validation
```bash
python code/cli/run_pipeline.py --stage download
python code/cli/run_pipeline.py --stage validate
```
*   This will attempt to download data from the NIST Internal Report series.
*   If the dataset is < 500 records or missing required fields, the script will **halt** and report `SchemaMismatchError`.
*   If NIST fails, it will attempt to load OpenCorrosion.
*   If both fail, it will generate synthetic data (Simulation Mode) or halt.

### Step 2: Model Training
```bash
python code/cli/run_pipeline.py --stage train
```
*   Trains Random Forest and Gradient Boosting models.
*   Uses "Leave-One-Specific-Alloy-Out" split (or GroupKFold fallback).
*   Logs metrics to `data/logs/pipeline.log`.

### Step 3: Evaluation & Interpretation
```bash
python code/cli/run_pipeline.py --stage evaluate
python code/cli/run_pipeline.py --stage interpret
```
*   Generates R², RMSE, and null baseline comparison.
*   Computes permutation importance with FDR correction.
*   Generates partial dependence plots (via `interpret.py`).

## Output Artifacts

*   `data/processed/clean_dataset.parquet`: Cleaned and split dataset.
*   `data/logs/schema_validation.log`: Log of validation steps.
*   `data/logs/pipeline.log`: Full execution log.
*   `results/metrics.json`: Final model performance metrics.
*   `results/feature_importance.png`: Visualization of top features.
*   `results/pdp_plots/`: Partial dependence plots for key interactions.

## Troubleshooting

*   **SchemaMismatchError**: The dataset downloaded has < 500 valid records or is inaccessible. This is a hard stop per the spec. Check the `data/logs/schema_validation.log` for details on missing fields.
*   **NIST-IR-8200 Unreachable**: If the download fails, check network connectivity. The pipeline will attempt OpenCorrosion or Simulation Mode.
*   **Memory Error**: Ensure the dataset is being streamed or chunked. If the raw file is too large, the `download_nist.py` script uses `streaming=True`.