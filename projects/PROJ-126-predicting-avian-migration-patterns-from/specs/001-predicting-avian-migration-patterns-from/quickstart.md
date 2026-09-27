# Quickstart: Predicting Avian Migration Patterns

## Prerequisites

-   Python 3.11+
-   Git
-   10GB free disk space (for raw data download)
-   8GB+ RAM (recommended for full processing; 7GB minimum with chunking)
-   **NASA Earthdata Token**: Obtain a token from https://urs.earthdata.nasa.gov/ and set it as an environment variable `NASA_EARTHDATA_TOKEN`.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-126-predicting-avian-migration-patterns-from
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

## Data Setup

The pipeline automatically downloads data from the verified sources.

1.  **Run the data loader**:
    ```bash
    python code/data_loader.py
    ```
    This script will:
    -   Download `train.csv` (EBD) from Hugging Face.
    -   Fetch environmental data (Temp, EVI) from NASA Earthdata (MODIS).
    -   Verify checksums.
    -   Store raw files in `data/raw/`.

    *Note: If the full continental MODIS dataset cannot be processed due to memory constraints, the script will automatically reduce the study scope to a verified regional subset (Pacific Northwest) and log a warning. **No synthetic data is generated.**.*

## Running the Pipeline

Execute the full end-to-end pipeline:

```bash
bash code/run_pipeline.sh
```

This script performs:
1.  **Preprocessing**: Aggregates EBD to 0.5° grid, calculates first arrival (sweep 3, 5, 10), and joins environmental data.
2.  **Training**: Trains XGBoost models (Temp-only, EVI-only, Combined) with temporal split.
3.  **Evaluation**: Runs Diebold-Mariano tests and Permutation Importance.
4.  **Visualization**: Generates SHAP plots and migration maps.
5.  **Feasibility**: Measures runtime and memory usage (using `psutil`).

**Expected Outputs**:
-   `data/processed/first_arrival_sweep.csv`
-   `data/processed/metrics.json`
-   `data/outputs/shap_summary.png`
-   `data/outputs/migration_map.png`

## Verification

To verify the results:

1.  **Check Metrics**:
    ```bash
    cat data/processed/metrics.json
    ```
    Ensure `combined_model_rmse` is lower than `naive_baseline_rmse` and the `p_value_dm` is < 0.05.

2.  **Run Unit Tests**:
    ```bash
    pytest tests/ -v
    ```

## Troubleshooting

-   **OOM (Out of Memory)**: If the process crashes due to memory, the pipeline will automatically reduce the study scope to the Pacific Northwest region. If this fails, edit `code/config.py` and reduce `SAMPLE_SIZE` or enable `USE_DASK=True` (if installed).
-   **Data Download Failure**: Verify your internet connection. The script retries 3 times. If it fails, check the firewall or proxy settings.
-   **NASA Earthdata API Error**: Ensure the `NASA_EARTHDATA_TOKEN` environment variable is set correctly. If the API is down, the pipeline will fail with a clear error message.
