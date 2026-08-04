# Quickstart: Predicting Chemical Reaction Yields from Spectroscopic Data

## Prerequisites

*   Python 3.11+
*   pip / poetry
*   Sufficient disk space (for datasets and artifacts)
*   Internet connection (for downloading datasets)

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
    *Note: `requirements.txt` pins versions of `torch` (CPU), `rdkit`, `pandas`, `pyarrow`, etc.*

## Data Download & Preprocessing

The pipeline automatically downloads datasets from Hugging Face if `data/raw/` is empty.

1.  **Run the ingestion script**:
    ```bash
    python src/cli/main.py --stage ingest
    ```
    *This will download DFT data, verify checksums, and log to `state/...yaml`.*

2.  **Run the preprocessing pipeline**:
    ```bash
    python src/cli/main.py --stage preprocess
    ```
    *This resamples spectra, computes fingerprints, splits by template, and generates the leakage report.*

## Training

Run the training script. By default, it uses the CPU and stops after a predefined number of epochs or early stopping.

```bash
python src/cli/main.py --stage train
```

*   **Output**: Model weights saved to `data/artifacts/model_best.pt` and training logs to `data/artifacts/training_log.json`.
*   **Time Estimate**: ~2-4 hours on a standard CPU runner.

## Evaluation & Interpretability

Run the evaluation script to generate metrics, baselines, and attention heatmaps.

```bash
python src/cli/main.py --stage evaluate
```

*   **Output**:
    *   `data/artifacts/metrics.json`: RMSE, MAE, R² for all models.
    *   `data/artifacts/attention_heatmaps.png`: Visualizations of spectral importance.
    *   `data/artifacts/leakage_report.json`: Verification of split integrity.
    *   `data/artifacts/integrity_report.json`: Simulated Data Integrity Check results.
    *   `data/artifacts/vif_report.json`: Collinearity check results.
    *   `data/artifacts/simulated_validation_report.json`: Limitation note for simulated data.

## Reproducibility

To ensure full reproducibility, set the seed explicitly:

```bash
export PYTHONHASHSEED=42
export RANDOM_SEED=42
python src/cli/main.py --stage train
```

## Troubleshooting

*   **OOM (Out of Memory)**: If you encounter memory errors, reduce `BATCH_SIZE` in `src/config/defaults.yaml` to 16 or 8.
*   **Missing Datasets**: If a download fails, check your internet connection. The script retries a limited number of times.
*   **CUDA Errors**: This project is CPU-first. If you see CUDA errors, ensure `torch` was installed as the CPU version (check `requirements.txt`).