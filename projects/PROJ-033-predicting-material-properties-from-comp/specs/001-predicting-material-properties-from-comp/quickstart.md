# Quickstart: Predicting Material Properties from Compositional Data with Graph Neural Networks

## Prerequisites
- Python 3.11, git, internet access (only needed to install dependencies; dataset must be supplied per the data contract)

## Setup
```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 1. Provide the dataset
Place a CSV or Parquet file that conforms to `contracts/materials_dataset.schema.yaml` (columns `material_id, formula, band_gap, hardness, crystal_system`) at `data/raw/materials.csv`. The loader will compute a SHA‑256 checksum and record it.

## 2. Ingest, validate & clean
```bash
python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv
```
This command loads the data in chunks (≤ 5 000 rows), validates each row against the schema, drops rows with missing required fields, removes duplicates, applies the 1.5 × IQR outlier filter for `band_gap` and `hardness`, and writes the cleaned dataset.

## 3. Train the composition‑only GNN (CPU)
```bash
python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42
```
Performs 5‑fold crystal‑system‑stratified cross‑validation, uses Adam (lr = 1e‑3), early stopping (patience = 10), and respects the runtime guards (30 min per epoch warning, 6 h total limit). Graphs are cached under `data/processed/graphs/`.

## 4. Evaluate
```bash
python src/training/evaluate.py --metrics_out data/results_composition_only.json
```
Emits R², MAE, and RMSE (mean ± std) for band gap and hardness, a Random Forest baseline, the `delta_vs_rf` baseline gap, and per‑crystal‑system metrics (`data/metrics_by_system.csv`). The reported “fold‑disagreement band” is mean ± 1.96 × std of the fold predictions.

## 5. Inference on a new formula
```bash
python src/inference/predict.py --formula "Fe2O3" --out data/predictions.json
```
Returns predicted band gap and hardness together with a timestamp and the fold‑disagreement band across the 5 checkpoints.

## 6. Interpretability (optional)
```bash
python src/interpret/extract_embeddings.py --out outputs/node_embeddings.npy
python src/interpret/pca_correlation.py --report_out interpretability_report.md
```

## 7. Run the test suite
```bash
pytest -q tests/
```
Contract tests validate the JSON schemas; unit tests cover the loader, graph builder, split logic, runtime guard, and inference using bundled fixtures.

## Outputs
- `data/results_composition_only.json` – model metrics (schema‑validated)
- `data/metrics_by_system.csv` – per‑crystal‑system performance
- `data/predictions.json` – inference result for a new formula
- `interpretability_report.md` – PCA‑correlation analysis (optional)
- `outputs/gnn_checkpoint_<hash>.pt`, `outputs/node_embeddings.npy` – model checkpoints and embeddings

**Known limitations**: (1) a verified open dataset with the required columns must be supplied; (2) the structure‑aware baseline is not executed because an open CIF source is unavailable; (3) spec deviations (additional element‑fraction node feature, fold‑disagreement band labeling) are documented in `plan.md`.