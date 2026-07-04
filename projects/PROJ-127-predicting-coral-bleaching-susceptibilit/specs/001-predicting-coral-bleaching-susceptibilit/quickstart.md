# Quickstart: Predicting Coral Bleaching Susceptibility

## Prerequisites

- Python 3.11+
- Git
- Access to the verified dataset URLs (internet connection required for initial download).

## Installation

1.  **Clone the repository** and navigate to the project root.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `xgboost`, `scikit-learn`, `pandas`, `geopandas`, `rasterio`, and `numpy`.*

## Running the Pipeline

The pipeline is executed via the `main.py` script, which orchestrates ingestion, training, and evaluation.

```bash
python code/main.py
```

### What this does:
1.  **Downloads Data**: Fetches verified NOAA/UNEP data from HuggingFace.
2.  **Data Gap Check**: Verifies if Coral Trait Database and ReefBase data are available. **If missing, the script halts and generates a Data Gap Report.**
3.  **Preprocesses**: Imputes missing values, calculates VIF, and drops collinear features.
4.  **Trains**: Fits an XGBoost model with spatial hold-out (West vs. East) **only if real data is present**.
5.  **Evaluates**: Computes ROC-AUC, FDR-corrected feature importance, bootstrap stability, and threshold sensitivity (including variation metric).
6.  **Maps**: Generates a GeoTIFF risk map for the target region.

### Simulation Mode (Opt-In Only)
To run the pipeline with synthetic data for testing purposes only (not for scientific claims):
```bash
python code/main.py --simulation-mode
```
**Warning**: In simulation mode, spatial hold-out and statistical validation are disabled. All outputs are labeled "Simulation Only".

## Expected Outputs

- `data/processed/unified_dataset.parquet`: The cleaned, feature-engineered dataset (if real data available).
- `data/models/xgboost_model.json`: The trained model artifact (if real data available).
- `results/feature_importance.csv`: Permutation importance with FDR-corrected p-values (if real data available).
- `results/risk_map.tif`: The spatial risk map (GeoTIFF) (if real data available).
- `results/threshold_sensitivity.csv`: FP/FN rates and variation metric for cutoffs 0.3, 0.5, 0.7.
- `data/data_gap_report.md`: Generated if required data is missing.

## Troubleshooting

- **Runtime Error (RAM)**: If the process exceeds 7 GB RAM, the script automatically reduces the spatial sample size. If it fails, check `code/config.py` and reduce `SAMPLE_SIZE`.
- **Missing Data**: If the verified URLs for traits/labels are unavailable, the script will **HALT** and generate a `data_gap_report.md`. It will **not** proceed with synthetic data.
- **No GPU**: Ensure no CUDA-specific code is imported. The script enforces CPU-only execution.
