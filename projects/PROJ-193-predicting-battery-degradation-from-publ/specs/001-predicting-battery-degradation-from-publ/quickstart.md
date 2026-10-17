# Quickstart: End‑to‑End Battery Degradation Prediction

This guide walks a new researcher through the full pipeline on a fresh GitHub Actions runner (or local Linux environment).

## Prerequisites
```bash
# Clone the repository
git clone https://github.com/your-org/battery-degradation.git
cd battery-degradation

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Step 1 – Data Ingestion
```bash
python -m src.data.ingest \
    --output data/raw/ \
    --log-level INFO
```
- Downloads the verified placeholder CSVs.
- Verifies checksums (stored in `state/...yaml`).
- Filters out rows missing any required column.

## Step 2 – Preprocessing
```bash
python -m src.data.preprocess \
    --input data/raw/ \
    --output data/processed/processed_v1.npz \
    --seed 42
```
- Resamples each trace to 100 time‑steps per cycle.
- Normalizes using statistics from cycles 1‑50 only.
- Saves a NumPy `.npz` file conforming to `contracts/processed_dataset.schema.yaml`.

## Step 3 – Model Training
```bash
python -m src.model.train \
    --data data/processed/processed_v1.npz \
    --output models/bilstm_v1.pt \
    --log-level INFO \
    --max-runtime 1800   # 30 min hyperparameter sweep limit
```
- Performs a limited grid search.
- Early stopping on a [deferred] validation split.
- Logs final validation R² and training duration.

## Step 4 – Baseline Comparison
```bash
python -m src.model.baseline \
    --data data/processed/processed_v1.npz \
    --output models/baseline_v1.pkl
```
- Trains a linear regression on hand‑crafted incremental‑capacity features.
- Prints baseline R² for comparison.

## Step 5 – Evaluation & Uncertainty
```bash
python -m src.model.evaluate \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output results/predictions.json
```
- Computes test‑set R², RMSE, and [deferred] Monte‑Carlo dropout intervals.
- Generates `results/metrics.json` and validates against `contracts/model_output.schema.yaml`.

## Step 6 – Interpretability
```bash
# SHAP summary
python -m src.interpret.shap_analysis \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output figures/shap_summary.png

# Permutation importance
python -m src.interpret.permutation_importance \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output figures/permutation_importance.csv

# Attention weights
python -m src.interpret.attention_attribution \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output figures/attention_heatmap.png
```
- All figures are saved under `figures/` and referenced directly in the manuscript.

## Step 7 – Verification
Run contract tests to ensure artifact compliance:
```bash
pytest -q tests/contract/test_processed_schema.py
pytest -q tests/contract/test_model_output_schema.py
```

## Step 8 – Review Outputs
- `results/metrics.json` contains R², RMSE, CI coverage.
- `figures/` hold SHAP, permutation, and attention visualizations.
- `contracts/` schemas can be inspected to confirm structure.

All steps are deterministic (seeds fixed) and reproducible on the GitHub Actions free tier. For CI integration, add the above commands to `.github/workflows/research.yml` in the appropriate order.

> **Disclaimer:** Because the current dataset is a placeholder lacking true voltage/current/temperature traces and a genuine capacity‑fade target, the reported metrics are illustrative only and do not constitute scientific evidence. Replace the placeholder with a real multi‑channel battery dataset to obtain valid results.
