# Quickstart: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face datasets (no login required for public datasets)

## Installation

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

1. **Run Ingestion Script**:
   ```bash
   python src/cli/main.py --step ingestion
   ```
   - Downloads datasets from verified Hugging Face URLs.
   - Generates checksums in `state/artifact_hashes.yaml`.

2. **Run Preprocessing Script**:
   ```bash
   python src/cli/main.py --step preprocessing
   ```
   - Resamples spectra, normalizes, computes fingerprints.
   - **Generates Synthetic Yield** from descriptors.
   - Splits data by reaction template.
   - Outputs `data/processed/` and `data/artifacts/leakage_report.json`.

## Model Training

1. **Train Attention Model**:
   ```bash
   python src/cli/main.py --step train --model attention
   ```
   - Trains on CPU (or GPU if available).
   - Saves model to `data/artifacts/model_checkpoint.pth`.

2. **Train Baselines**:
   ```bash
   python src/cli/main.py --step train --model baseline
   ```

## Evaluation

1. **Run Evaluation**:
   ```bash
   python src/cli/main.py --step evaluate
   ```
   - Computes RMSE, MAE, R².
   - Performs t-tests, permutation tests, **Partial Correlation**.
   - **Integrity Check**: Verifies yield not a function of spectra.
   - Generates attention heatmaps.
   - Outputs `data/artifacts/metrics.json`, `data/artifacts/integrity_report.json`.

2. **View Results**:
   - Metrics: `data/artifacts/metrics.json`
   - Heatmaps: `data/artifacts/heatmaps/`
   - Leakage Report: `data/artifacts/leakage_report.json`
   - Integrity Report: `data/artifacts/integrity_report.json`

## Reproducibility

- **Random Seeds**: All seeds are pinned in `src/utils/seeds.py`.
- **Data Versioning**: Checksums recorded in `state/artifact_hashes.yaml`.
- **Re-run**: `python src/cli/main.py --step all` to run full pipeline.

## Troubleshooting

- **OOM Error**: Reduce `batch_size` in `config/defaults.yaml`.
- **Data Download Failed**: Check internet connection; verify Hugging Face URLs.
- **Template Leakage**: Check `data/artifacts/leakage_report.json` for errors.