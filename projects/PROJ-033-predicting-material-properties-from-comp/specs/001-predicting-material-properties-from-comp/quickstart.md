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
Place a CSV/parquet conforming to `contracts/materials_dataset.schema.yaml` (columns `material_id, formula, band_gap, hardness, crystal_system`) at `data/raw/materials.csv`. The loader checksums it (SHA-256) and records the hash. **Note**: no verified open source for this data was available at planning time — see `research.md` Limitations.

## 2. Ingest, validate & clean
```bash
python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv
```
Chunked loading keeps peak RAM ≤ 6 GB; invalid rows are dropped with warnings; rows outside 1.5×IQR of either target are dropped with a logged count (per the spec's Assumptions) and the cleaned data is written to a new file.

## 3. Train the composition-only GNN (CPU)
```bash
python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42
```
5-fold crystal-system-stratified CV; Adam lr=1e-3; early stopping patience=10; 30-min/epoch warning and 6-h halt guards active. Composition graphs are built in-memory and cached under `data/processed/graphs/`.

## 4. Evaluate
```bash
python src/training/evaluate.py --metrics_out data/results_composition_only.json
```
Emits R²/MAE/RMSE (mean ± std) for band gap and hardness, the Random Forest baseline comparison (`rf_baseline` and `delta_vs_rf` blocks — a baseline gap, not a structure information-loss ΔR²), and `data/metrics_by_system.csv`. The mean ± 1.96 × std-of-folds quantity is labeled a **fold-disagreement band**, not a calibrated [deferred] prediction interval.

## 5. Inference on a new formula
```bash
python src/inference/predict.py --formula "Fe2O3" --out data/predictions.json
```
Returns predicted band gap and hardness with a timestamp and the fold-disagreement band across the 5 fold checkpoints.

## 6. Interpretability
```bash
python src/inference/../interpret/extract_embeddings.py --out outputs/node_embeddings.npy
python src/interpret/pca_correlation.py --report_out interpretability_report.md
```

## 7. Run the test suite
```bash
pytest -q tests/
```
Contract tests validate both schemas; unit tests cover the graph builder, structure graph, splits, runtime guards, and inference using bundled fixtures (fixtures validate software only; they are never reported as study results).

## Outputs
- `data/results_composition_only.json` — metrics incl. `delta_vs_rf` (schema-validated)
- `data/metrics_by_system.csv` — per-crystal-system performance
- `data/predictions.json` — new-formula inference with fold-disagreement band
- `interpretability_report.md` — PCA/correlation analysis (held-out properties only)
- `outputs/gnn_checkpoint_<hash>.pt`, `outputs/node_embeddings.npy`

**Known limitations**: (1) no verified open dataset with the required variables existed at planning time — the scientific run is gated on scope revision; (2) the structure-aware baseline (spec FR-005/FR-006/FR-011) is not executed — the Materials Project CIF API is credential-gated and no open verified CIF source exists, so ΔR² information loss (SC-002) is not reported; (3) planned spec deviations (FR-002 feature list, FR-006 shared test set, FR-007 interval labeling) are flagged for kickback in `plan.md`.