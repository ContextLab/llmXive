# Quickstart: Predicting Avian Migration Patterns

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended for CI compatibility).
- **Memory**: Minimum 8 GB RAM recommended (A fixed upper bound is imposed on CI resources.; local dev should have headroom).
- **Disk**: 20 GB free space for raw and processed data.

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for reproducibility (Constitution Principle I).*

## Running the Pipeline

The pipeline is executed via a single shell script that orchestrates data loading, preprocessing, training, and evaluation.

```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

### What the script does:
1.  **Downloads Data**: Fetches EBD and MODIS data from the verified HuggingFace URLs (streaming enabled for EBD).
2.  **Preprocessing**:
    - Filters eBird for complete checklists.
    - Aggregates to regular grid cells.
    - Calculates "first arrival" for thresholds 3, 5, and 10.
    - Joins with lagged MODIS data.
    - Applies VIF filtering to remove collinear features.
3.  **Modeling**:
    - Trains XGBoost models (Temp-only, NDVI-only, Combined).
    - Performs temporal split (Train: 2015-2020, Val: 2021, Test: subsequent period).
    - Computes SHAP values and Permutation Importance.
    - Runs Diebold-Mariano test on temporal aggregates.
4.  **Stability & Performance**:
    - Analyzes stability across thresholds {3, 5, 10} and flags if variation > 7 days.
    - Measures runtime and RAM usage, writing logs to `data/outputs/feasibility.log`.
5.  **Output Generation**:
    - Saves metrics to `data/outputs/metrics.json`.
    - Saves feature importance to `data/outputs/feature_importance.csv`.
    - Generates regional maps and stability reports in `data/outputs/`.

## Expected Outputs

After successful completion, the following files will be generated:

- `data/processed/grid_cell_data.parquet`: The unified spatiotemporal dataset.
- `data/processed/first_arrival_sweep.csv`: Arrival dates for thresholds 3, 5, 10.
- `data/outputs/metrics.json`: RMSE, Pearson R, and DM p-values.
- `data/outputs/stability_report.json`: Variation in arrival dates across thresholds.
- `data/outputs/feasibility.log`: Runtime and RAM usage logs.
- `data/outputs/shap_summary.png`: SHAP summary plot.
- `data/outputs/permutation_importance.csv`: Robust feature rankings.
- `data/outputs/regional_maps.png`: Visualizations of predicted arrival dates.

## Troubleshooting

- **OOM (Out of Memory)**: If the process crashes with `MemoryError`, ensure you are using the streaming version of the EBD loader (default). Reduce `max_depth` in `config.py` if training fails.
- **Data Missing**: If `first_arrival_sweep.csv` is empty, check if the verified MODIS dataset covers the geographic region of the eBird data. (Note: The verified MODIS dataset is a "Lake Powell toy dataset"; if the eBird data is outside this region, the join will fail for most cells. The pipeline will log this and proceed with available data).
- **Network Error**: Ensure the GitHub Actions runner (or local machine) has internet access to fetch from HuggingFace.
- **Validation Error**: If the pipeline fails at the start, check if the verified EBD subset contains *Setophaga ruticilla* and the years 2015-2023.

## Verification

To verify the pipeline ran correctly:
1.  Check `data/outputs/metrics.json` for non-null `rmse` and `dm_p_value`.
2.  Ensure `data/processed/first_arrival_sweep.csv` contains rows for all three thresholds (3, 5, 10).
3.  Confirm `data/outputs/stability_report.json` exists and contains a `variation_days` field.
4.  Check `data/outputs/feasibility.log` to confirm runtime ≤ 6 hours and RAM ≤ 7 GB.
5.  Confirm `data/outputs/permutation_importance.csv` lists both `temperature` and `ndvi` features.