# Quickstart: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Prerequisites

*   Python 3.11+
*   API Keys (Optional but recommended for full data):
    *   Materials Project API Key (`MP_API_KEY`)
    *   AFLOWlib API Key (`AFLOW_API_KEY`)
*   (Optional) If keys are missing, the pipeline will automatically fall back to the verified Zenodo dataset (Zhang et al., 2020).

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Configuration

Set your API keys as environment variables (optional):

```bash
export MP_API_KEY="your_mp_key_here"
export AFLOW_API_KEY="your_aflow_key_here"
```

*Note: If keys are not set, the script will log a warning and automatically attempt to download the verified Zenodo dataset as a fallback.*

## Running the Pipeline

Execute the main pipeline script:

```bash
python code/ingestion/fetch_data.py
python code/features/descriptors.py
python code/modeling/train.py
python code/modeling/evaluate.py
```

Or run the end-to-end runner (if available):

```bash
python code/run_pipeline.py
```

## Expected Outputs

1.  **Data**: `data/processed/clean_mg_data.parquet`
2.  **Models**: `models/linear_regression.pkl`, `models/random_forest.pkl`, `models/null_model.pkl`
3.  **Metrics**: `results/metrics.json` (containing R², MAE, RMSE, p-values, and analysis type)
4.  **Logs**: `logs/pipeline.log` (including warnings about missing data, API failures, VIF exclusions, or "No Data" status)

## Verification

Check the `results/metrics.json` file.
*   If `analysis_type` is "Quantitative" and `p_value` < 0.05 and `r2` > 0.3, the model is statistically significant.
*   If `analysis_type` is "Qualitative" (N < 50), review the `feature_importance` and `divergence_flag` for trend insights.
*   If `analysis_type` is "NoData", the pipeline completed successfully but found no valid entries in API or Zenodo.

## Troubleshooting

*   **No Data Found**: If the pipeline stops with "No amorphous entries found," it will automatically fall back to the Zenodo dataset. If that also fails, check your internet connection.
*   **Memory Error**: If running on a local machine with low RAM, the script attempts to stream data. If this fails, reduce the dataset size manually in `code/ingestion/fetch_data.py`.
*   **VIF Warning**: If `size_mismatch` is excluded, it is due to high multicollinearity. This is expected and ensures valid results.