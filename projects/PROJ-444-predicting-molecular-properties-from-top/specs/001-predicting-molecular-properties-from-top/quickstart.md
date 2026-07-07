# Quickstart: Predicting Molecular Properties from Topological Data Analysis

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Access to GitHub Actions runner (for CI execution) or local Linux environment.

## Installation

1.  **Clone Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-444-predicting-molecular-properties-from-top
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
    *Note: Ensure `gudhi` or `dionysus2` installs CPU wheels. If GPU wheels are detected, force CPU installation.*

## Data Preparation

1.  **Download Dataset**:
    The pipeline expects data in `data/raw/`. Use the script to fetch from verified sources:
    ```bash
    python code/01_data_ingestion.py --source pubchem
    ```
    *Verify that the downloaded file contains `smiles` and target property columns.*

2.  **Validate Data**:
    The script automatically logs invalid SMILES. Check `data/processed/exclusion_log.csv`.

## Running the Pipeline

Execute the steps sequentially:

1.  **Compute Checksums**:
    ```bash
    python code/00_checksum_verify.py
    ```
    *Output: `data/checksums.txt`*

2.  **Compute TDA Features**:
    ```bash
    python code/02_tda_computation.py --resolution 10
    ```
    *Output: `data/processed/topological_features.csv`*

3.  **Train & Evaluate Models**:
    ```bash
    python code/04_model_training.py
    ```
    *Output: `reports/metrics/` with R², RMSE, and p-values.*

4.  **Run Diagnostics**:
    ```bash
    python code/06_diagnostics.py
    ```
    *Output: `reports/diagnostics/vif_report.json`, `reports/diagnostics/mi_report.json`*

5.  **Sensitivity Analysis** (Optional):
    ```bash
    python code/05_sensitivity_analysis.py --resolutions 10 20 30
    ```

6.  **Monitor Resources** (Required for SC-004):
    ```bash
    python code/07_resource_monitor.py
    ```
    *Output: `reports/metrics/resource_usage.json`*

## Verification

-   **Contract Tests**: Run `pytest tests/contract/` to validate output schemas.
-   **Reproducibility**: Re-run the pipeline; results should match (within floating-point tolerance) due to pinned seeds.