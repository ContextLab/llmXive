# Quickstart: Predicting Molecular Conductivity from Graph-Based Features

## Prerequisites
*   Python 3.11+
*   Git
*   Access to Hugging Face (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-528-predicting-molecular-conductivity-from-g
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is designed to run sequentially. Execute the following commands in order:

1.  **Download Data**:
    ```bash
    python code/01_download_data.py
    # Output: data/raw/*.parquet
    ```

2.  **Compute Descriptors**:
    ```bash
    python code/02_compute_descriptors.py
    # Output: data/processed/descriptors_base.csv, data/processed/descriptors.csv
    ```

3.  **Preprocess & Split**:
    ```bash
    python code/03_preprocess.py
    # Output: data/processed/cleaned.csv
    ```

4.  **Train Models**:
    ```bash
    python code/04_train_models.py
    # Output: data/processed/model_results.json
    ```

5.  **VIF Analysis & Retraining**:
    ```bash
    python code/05_vif_analysis.py
    # Output: data/processed/vif_iteration_log.json
    ```

6.  **Feature Importance**:
    ```bash
    python code/06_feature_importance.py
    # Output: data/processed/feature_importance.csv
    ```

7.  **Sensitivity Analysis**:
    ```bash
    python code/07_sensitivity_analysis.py
    # Output: data/processed/sensitivity_results.json
    ```

8.  **Generate Visualizations**:
    ```bash
    python code/08_visualization.py
    # Output: figures/*.png
    ```

## Verification

To verify the pipeline completed successfully:
*   Check that `data/processed/descriptors_base.csv` exists and has > 0 rows.
*   Check that `data/processed/vif_iteration_log.json` contains the final VIF scores.
*   Check that `figures/` contains correlation plots.
*   Run `pytest tests/` to execute unit and integration tests.

## Troubleshooting

*   **RDKit Import Error**: Ensure `rdkit` is installed via `conda` or `pip` (check `requirements.txt`).
*   **Dataset Download Failed**: Verify internet connectivity and Hugging Face access. The script uses `streaming=True` to handle large files.
*   **Memory Error**: If running out of RAM, reduce the `batch_size` in `01_download_data.py` or `02_compute_descriptors.py`.
