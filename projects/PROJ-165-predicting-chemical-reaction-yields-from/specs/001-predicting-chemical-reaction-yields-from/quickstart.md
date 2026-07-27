# Quickstart: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## Prerequisites
- Python 3.11+
- Git
- ~ GB Disk Space
- Internet Access (for dataset download)

## Installation

1.  **Clone & Setup**
    ```bash
    git clone <repo-url>
    cd <project-root>
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Environment**
    ```bash
    python -c "import torch; print(torch.__version__); print('CPU' if not torch.cuda.is_available() else 'GPU')"
    ```

## Running the Pipeline

### Step 1: Data Ingestion & Preprocessing
Downloads verified datasets, filters for **real paired data** (SMILES + Spectrum + Yield), resamples, and splits by template.
**Note**: Samples without real spectra are excluded. If the final dataset size is < 500, the pipeline halts and generates a Data Insufficiency Report.
```bash
python -m src.cli.main ingest
python -m src.cli.main preprocess
```
*Outputs*: `data/processed/train.parquet`, `data/processed/test.parquet`, `data/artifacts/leakage_report.json`, or `data/artifacts/data_insufficiency_report.json`.

### Step 2: Model Training (Conditional)
Trains the attention model with early stopping. **Only runs if data sufficiency check passes.**
```bash
python -m src.cli.main train
```
*Outputs*: `models/best_model.pt`, `data/artifacts/training_log.json`.

### Step 3: Evaluation & Interpretability
Runs baselines, computes metrics, performs permutation tests, and generates heatmaps. **Only runs if data sufficiency check passes.**
```bash
python -m src.cli.main evaluate
```
*Outputs*: `data/artifacts/evaluation_report.json`, `figures/attention_heatmap.png`.

## Testing

Run unit and integration tests:
```bash
pytest tests/ -v --cov=src
```

## Troubleshooting

- **Data Insufficiency**: If the pipeline halts with "Data Insufficiency", check `data/artifacts/data_insufficiency_report.json` for the count of real paired samples. The project cannot proceed with quantitative analysis if N < 500.
- **Memory Error**: Reduce `batch_size` in `config/default.yaml` to 16.
- **Dataset Missing**: Ensure internet connection; check `data/raw/` for checksums.
- **Leakage Detected**: If `leakage_report.json` shows overlap, re-run `preprocess` with a different random seed or check template extraction logic.