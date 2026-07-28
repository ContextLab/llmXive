# Quickstart: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

This guide walks you through the end-to-end execution of the HEA yield strength prediction pipeline.

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local Linux environment with ~7 GB RAM.

## Step 1: Environment Setup

1.  Clone the repository and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-418-predicting-the-yield-strength-of-high-en
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

The pipeline attempts to download data from the verified source: `materialsproject/hea-yield-strength` on HuggingFace.

1.  **Download Data**:
    ```bash
    python code/data_acquisition.py
    ```
    *Output*: `data/raw/hea_data.parquet` (if available) or a log indicating N=0 if the dataset is unreachable.

2.  **Verify Data**:
    Check `data/raw/` for the downloaded file. Ensure it contains `composition`, `yield_strength`, and `phase` columns.

## Running the Pipeline

Execute the full pipeline (acquisition, descriptors, training, validation):

```bash
python code/main.py --stage fetch
```

### What happens?
1.  **Acquisition**: Downloads and filters data from `materialsproject/hea-yield-strength` (FR-001, FR-003).
2.  **Descriptors**: Calculates δ, Δχ, VEC, etc. using `contracts/elemental_properties.schema.yaml` (FR-002).
3.  **Training**: Trains RF, GB, Linear models (FR-004).
4.  **Validation**: Runs permutation tests, bootstrap, VIF (FR-006..FR-012).
5.  **Output**: Saves `output/metrics.json` and `output/plots/`.

## Expected Outputs

- **`output/metrics.json`**: Contains R², MAE, RMSE for all models.
- **`output/plots/`**: Feature importance plots, residual plots (with disclaimer).
- **`output/reports/statistical_summary.md`**: Detailed statistical validation results.

## Troubleshooting

- **N=0 Error**: If the pipeline exits with "N=0", the verified dataset `materialsproject/hea-yield-strength` was unreachable or empty. This is a data limitation, not a code error.
- **Memory Error**: Ensure you are on a machine with ≥7 GB RAM. If running on GitHub Actions, the default runner provides this.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt`.

## Validation

To verify the pipeline:
1.  Run `pytest tests/` to ensure all unit and integration tests pass.
2.  Check `output/metrics.json` for valid float values (no NaN).
3.  Verify that all plots contain the disclaimer: "Associational analysis only; no causal inference".