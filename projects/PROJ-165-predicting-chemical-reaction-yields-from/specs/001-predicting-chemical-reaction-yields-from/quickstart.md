# Quickstart: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions runner (or local environment with 8GB+ RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-165-predicting-chemical-reaction-yields-from
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r src/requirements.txt
    ```

## Running the Pipeline

The entire pipeline (Data Generation -> Preprocessing -> Training -> Evaluation) can be run via the CLI:

```bash
python src/cli/main.py --run-full
```

### Steps Executed

1.  **Data Generation**:
    -   Generates synthetic dataset (several thousand reactions) using physics-based simulator with stochastic noise.
    -   Computes and logs checksums.
    -   Performs Simulated Data Integrity Check (FR-015).
    -   *Output*: `data/raw/synthetic_data.parquet`, `state/artifact_hashes.yaml`.

2.  **Preprocessing**:
    -   Resamples spectra to fixed grids (IR/Raman/NMR).
    -   Generates ECFP4 fingerprints.
    -   Splits data by reaction template AND condition bucket (zero leakage).
    -   *Output*: `data/processed/train.parquet`, `data/processed/val.parquet`, `data/processed/test.parquet`, `data/artifacts/leakage_report.json`.

3.  **Training**:
    -   Trains the attention model and baselines.
    -   Saves checkpoints and logs.
    -   *Output*: `data/artifacts/model_weights.pth`, `data/artifacts/training_log.json`.

4.  **Evaluation**:
    -   Computes RMSE, MAE, R².
    -   Performs t-tests, Wilcoxon tests, and permutation tests.
    -   Computes VIF and attention correlations.
    -   Generates attention heatmaps (Top 1%, 5%, 10% thresholds).
    -   *Output*: `data/artifacts/evaluation_report.json`, `data/artifacts/attention_plots/`.

## Verifying Results

To verify reproducibility, run the pipeline again with the same seed:

```bash
python src/cli/main.py --run-full --seed 42
```

Compare the checksums in `state/artifact_hashes.yaml` and the metrics in `data/artifacts/evaluation_report.json` to ensure they match.

## Troubleshooting

-   **OOM Errors**: If you encounter Out-of-Memory errors, reduce the `batch_size` in `src/models/attention_net.py` or enable streaming in `src/data/ingestion.py`.
-   **High Collinearity**: If VIF > 5, check the simulation parameters in `src/data/ingestion.py` to ensure sufficient stochastic noise is injected.