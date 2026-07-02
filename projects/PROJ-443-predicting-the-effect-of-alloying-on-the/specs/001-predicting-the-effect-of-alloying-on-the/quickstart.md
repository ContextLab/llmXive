# Quickstart: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the OQMD dataset (via the provided HuggingFace URLs).

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions to ensure reproducibility on the CPU-only runner.*

## Running the Pipeline

The entire pipeline can be executed via the main script:

```bash
python code/main.py
```

This command performs the following steps sequentially:
1.  **Data Ingestion**: Downloads and filters OQMD data for HEAs.
2.  **Feature Engineering**: Computes descriptors and applies ILR transformation.
3.  **Model Training**: Trains RF, GB, and ElasticNet models.
4.  **Evaluation**: Performs grouped bootstrapping and FDR correction.
5.  **Reporting**: Generates `results/metrics.yaml` and plots.

### Running Specific Stages

- **Data Ingestion Only**:
  ```bash
  python code/data_ingestion.py --output data/processed/hea_samples_raw.csv
  ```
- **Model Training Only** (requires processed data to exist):
  ```bash
  python code/models.py --input data/processed/hea_features.csv
  ```

## Verifying Results

After the pipeline completes, verify the output:

1.  Check `results/metrics.yaml` for the performance metrics of all three models.
2.  Inspect `results/plots/` for parity plots and SHAP summaries.
3.  Confirm that the log output indicates "Dataset sufficiency check: PASSED" (≥500 samples).

## Troubleshooting

- **Error: "Insufficient samples"**: The OQMD source did not yield ≥500 HEA samples with elastic constants. This is a fatal error per Edge Case 1. The pipeline will halt and report the count.
- **Error: "Singularity in matrix"**: The ILR transformation was not applied correctly. Ensure `feature_engineering.py` is running before model training.
- **Memory Error**: The dataset is too large for the 7GB RAM limit. The pipeline should automatically sample or process in chunks; if not, check `config.py` for `max_samples` settings.
