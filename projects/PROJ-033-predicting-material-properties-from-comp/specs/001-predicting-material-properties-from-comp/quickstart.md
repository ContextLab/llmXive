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
Place a CSV or Parquet file that conforms to `contracts/materials_dataset.schema.yaml` (columns `material_id, formula, band_gap, hardness, crystal_system`) at `data/raw/materials.csv`. The loader will compute a SHA‑256 checksum and record it. (For software validation without a dataset, the bundled `tests/fixtures/tiny_materials.csv` exercises the same code path.)

## 2. Verify the contract tests (with evidence)
```bash
pytest tests/contract/ -q --junitxml=outputs/test_logs/phase0_contract.xml 2>&1 | tee outputs/test_logs/phase0_contract.log
```
The junit XML is the verification artifact proving the contract tests ran and passed.

## 3. Ingest, validate & clean
```bash
python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv 2>&1 | tee outputs/test_logs/loader.log
```
Loads in chunks (≤ 5 000 rows), validates each row, drops rows with missing required fields, deduplicates IDs, and applies the 1.5 × IQR outlier filter **per target** (`band_gap`, `hardness`) with per-target drop counts logged. **Metals (`band_gap == 0`) are valid and retained.**

## 4. Train the composition‑only GNN (CPU)
```bash
python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 2>&1 | tee outputs/test_logs/train_gnn.log
```
Performs 5‑fold crystal‑system‑stratified cross‑validation, uses Adam (lr = 1e‑3), early stopping (patience = 10), and respects the runtime guards (30 min per epoch warning, 6 h total limit). The log records the exit code; a non-zero exit is a failure, not a warning.

## 5. Evaluate
```bash
python src/training/evaluate.py --metrics_out data/results_composition_only.json 2>&1 | tee outputs/test_logs/evaluate.log
```
Emits R², MAE, and RMSE (mean ± std) for band gap and hardness, a Random Forest baseline, the `delta_vs_rf` baseline gap, and per‑crystal‑system metrics (`data/metrics_by_system.csv`). The reported "fold‑disagreement band" is mean ± 1.96 × std of the fold predictions.

## 6. Inference on a new formula
```bash
python src/inference/predict.py --formula "Fe2O3" --out data/predictions.json
```
Returns predicted band gap and hardness together with a timestamp and the fold‑disagreement band across the 5 checkpoints.

## 7. Interpretability (optional)
```bash
python src/interpret/extract_embeddings.py --out outputs/node_embeddings.npy
python src/interpret/pca_correlation.py --report_out interpretability_report.md
```

## 8. Run the full test suite (single verification artifact)
```bash
pytest tests/ -q --junitxml=outputs/test_logs/full_suite.xml 2>&1 | tee outputs/test_logs/full_suite.log
```
The junit XML is the authoritative record that the entire suite (contract + unit) passed.

## Outputs
- `data/results_composition_only.json` – model metrics (schema‑validated)
- `data/metrics_by_system.csv` – per‑crystal‑system performance
- `data/predictions.json` – inference result for a new formula
- `interpretability_report.md` – PCA‑correlation analysis (optional)
- `outputs/gnn_checkpoint_<hash>.pt`, `outputs/node_embeddings.npy` – model checkpoints and embeddings
- `outputs/test_logs/` – pytest junit XML and tee'd logs evidencing every run

**Known limitations**: (1) a verified open dataset with the required columns must be supplied, and hardness provenance documented; (2) the structure‑aware baseline is not executed because an open CIF source is unavailable; (3) spec deviations (additional element‑fraction node feature, fold‑disagreement band labeling) are documented in `plan.md`.
