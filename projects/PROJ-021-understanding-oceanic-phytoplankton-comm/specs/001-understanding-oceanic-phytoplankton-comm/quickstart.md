# Quickstart: Understanding Oceanic Phytoplankton Communities

## Prerequisites

*   Python 3.11+
*   Git
*   14GB free disk space
*   7GB RAM (recommended)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-021-understanding-oceanic-phytoplankton-comm
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end on a CPU-only environment.

1.  **Data Ingestion & Preprocessing**:
    ```bash
    python code/01_data_ingestion.py
    python code/02_preprocessing.py
    ```
    *Output*: `data/processed/aligned_dataset.csv`

2.  **Power Analysis & Scoping**:
    ```bash
    python code/02_preprocessing.py --power-analysis
    ```
    *Output*: `data/processed/power_analysis_report.json` (if N is insufficient, scoping is adjusted).

3.  **Model Training**:
    ```bash
    python code/03_model_training.py
    ```
    *Output*: `data/artifacts/rf_model.pkl`, `data/artifacts/vlm_model.pt`, `data/artifacts/training_logs.json`

4.  **Evaluation & Visualization**:
    ```bash
    python code/04_evaluation.py
    ```
    *Output*: `data/artifacts/feature_importance.png`, `data/artifacts/model_comparison_table.csv`

5.  **Versioning**:
    ```bash
    python code/05_versioning_state.py
    ```
    *Output*: Updated `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml` with content hashes.

## Verifying Results

Run the contract tests to ensure outputs match the schema:
```bash
pytest tests/contract/
```

Run the integration test to verify CPU feasibility:
```bash
pytest tests/integration/test_pipeline.py -v --tb=short
```

## Troubleshooting

*   **Memory Error**: Reduce the `BATCH_SIZE` in `code/utils/config.py` or enable `chunking` in the data loader.
*   **VLM Convergence Failure**: The script automatically falls back to the Random Forest baseline. Check `data/artifacts/training_logs.json` for the "early_stopping" flag.
*   **Missing Data**: If the aligned dataset has >5% missing values, the pipeline will exit with a warning. Check the `data/processed/missingness_report.csv`.
*   **Insufficient Power**: If the power analysis report indicates N is too low, the pipeline will log a warning and proceed with a reduced scope (single basin).