# Quickstart: Predicting Avian Migration Patterns

## Prerequisites

*   **Python**: 3.11+
*   **System**: Linux (or WSL2 on Windows).
*   **Memory**: 7 GB RAM minimum (for streaming processing).
*   **Disk**: 14 GB free space.

## Installation

1.  **Clone the Repository** (assuming the project is in the standard location):
    ```bash
    cd projects/PROJ-126-predicting-avian-migration-patterns-from
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Dependencies include: `pandas`, `xgboost`, `scikit-learn`, `scipy`, `shap`, `huggingface_hub`, `numpy`.*

## Data Setup

The pipeline is designed to download data automatically from the verified Hugging Face sources.

1.  **Run the Data Download Script**:
    ```bash
    python code/main.py --stage download
    ```
    *This will fetch the EBD and MODIS datasets to `data/raw/` and compute checksums.*

2.  **Verify Data Integrity**:
    Ensure the checksums match the expected values recorded in `state/...yaml`.

## Running the Pipeline

Execute the full pipeline (Download → Process → Train → Evaluate → Visualize):

```bash
python code/main.py --stage full
```

### Staged Execution

If you wish to run specific stages:

*   **Preprocessing only**:
    ```bash
    python code/main.py --stage preprocess
    ```
    *Outputs: `data/processed/grid_observations.csv`*

*   **Model Training only**:
    ```bash
    python code/main.py --stage train
    ```
    *Requires processed data. Outputs: `data/outputs/model.pkl`, `data/outputs/metrics.json`*

*   **Visualization only**:
    ```bash
    python code/main.py --stage viz
    ```
    *Outputs: `data/outputs/maps/`*

## Expected Outputs

After a successful run, check the `data/outputs/` directory:

*   `metrics.json`: Contains RMSE, Pearson correlation, and bootstrap p-values.
*   `feature_importance.json`: SHAP summary data.
*   `arrival_maps.png`: **Regional-scale map** of predicted arrival dates (Lake Powell region).
*   `sensitivity_analysis.csv`: Comparison of arrival dates across thresholds {3, 5, 10}.

## Troubleshooting

*   **MemoryError**: The pipeline uses streaming. If you encounter OOM, reduce the `grid_resolution` in `code/config.py` or ensure no other heavy processes are running.
*   **Data Download Failed**: Verify your internet connection. The EBD/MODIS sources are large; ensure the `huggingface_hub` library is up to date.
*   **Collinearity Warnings**: If SHAP values are unstable, check the `code/preprocessing.py` for the lag window configuration.

## Reproducibility

To ensure reproducibility, the random seed is pinned to `42` in `code/config.py`. Re-running the pipeline with the same data will produce identical results.
