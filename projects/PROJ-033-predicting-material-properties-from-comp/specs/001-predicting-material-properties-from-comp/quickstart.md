# Quickstart: Predicting Material Properties from Compositional Data with Graph Neural Networks

## Prerequisites
- Python 3.11, git, internet access (only needed to install dependencies; dataset must be supplied per the data contract)

## Setup
```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 1. Provide the dataset
Place the **Matbench Expt Gap** dataset file (`matbench_expt_gap.parquet`) that conforms to `contracts/materials_dataset.schema.yaml` at `data/raw/materials.parquet`. The loader will compute a SHA‑256 checksum and record it. If you prefer to use the tiny fixture for software validation, the bundled `tests/fixtures/tiny_materials.csv` exercises the same code path.

> **Note:** The hardness column is present but may contain `null` values because **no open dataset currently provides verified hardness measurements**. This limitation is documented in the plan and flagged for a future spec amendment.

## 2. Verify the contract tests (with evidence)
```bash
pytest tests/contract/ -q --junitxml=outputs/test_logs/contract.xml 2>&1 | tee outputs/test_logs/contract.log
```
The JUnit XML is the verification artifact proving the contract tests ran and passed.

## 3. Ingest, validate & clean
```bash
python src/data/loader.py --input data/raw/materials.parquet --out data/processed/materials_processed.csv 2>&1 | tee outputs/test_logs/loader.log
```
Loads in ≤5 000‑row chunks, validates each row, drops rows with missing required fields, deduplicates IDs, and applies the 1.5 × IQR outlier filter **per target independently** (`band_gap`, `hardness`). **Metals (`band_gap == 0`) are valid and retained**.

## 4. Train the composition‑only GNN (CPU)
```bash
python -m src.training.train_gnn --data data/processed/materials_processed.csv --seed 42 2>&1 | tee outputs/test_logs/train_gnn.log
```
Performs 5‑fold crystal‑system‑stratified cross‑validation, uses Adam (lr = 1e‑3), early stopping (patience = 10), and respects the runtime guards (30 min per epoch warning, 6 h total limit). The log records the exit code; a non‑zero exit is a failure, not a warning.

## 5. Train the structure‑aware GNN (CPU)
```bash
python -m src.training.train_structure_gnn --data data/processed/materials_processed.csv --seed 42 2>&1 | tee outputs/test_logs/train_structure_gnn.log
```

## 6. Evaluate
```bash
python -m src.training.evaluate --metrics_out data/results_composition_only.json 2>&1 | tee outputs/test_logs/evaluate.log
python -m src.training.evaluate_structure --metrics_out data/results_structure_aware.json --comparison_out data/comparison_summary.csv 2>&1 | tee outputs/test_logs/evaluate_structure.log
```

## 7. Inference on a new formula
```bash
python -m src.inference.predict --formula "Fe2O3" --out data/predictions.json
```

## 8. Interpretability (optional)
```bash
python -m src.interpret.extract_embeddings --out outputs/node_embeddings.npy
python -m src.interpret.pca_correlation --report_out interpretability_report.md
```

## 9. Run the full test suite (single verification artifact)
```bash
pytest tests/ -q --junitxml=outputs/test_logs/full_suite.xml 2>&1 | tee outputs/test_logs/full_suite.log
```

## Outputs
- `data/results_composition_only.json` – model metrics (schema‑validated)  
- `data/results_structure_aware.json` – model metrics for the structure‑aware baseline (hardness `null`)  
- `data/comparison_summary.csv` – ΔR², ΔMAE, ΔRMSE for band gap  
- `data/metrics_by_system.csv` – per‑crystal‑system performance  
- `data/predictions.json` – inference result for a new formula (hardness `null`)  
- `interpretability_report.md` – PCA‑correlation analysis (optional)  
- `outputs/gnn_checkpoint_<hash>.pt`, `outputs/structure_gnn_checkpoint_<hash>.pt`, `outputs/node_embeddings.npy` – model checkpoints and embeddings  
- `outputs/test_logs/` – pytest JUnit XML and tee‑ed logs evidencing every run  

**Known limitations**: (1) a verified open dataset with the required hardness column is missing; hardness values are `null` and will be added once such a dataset becomes available. (2) The structure‑aware baseline uses Matbench‑provided structures, satisfying Principle VI for band‑gap; full information‑loss quantification for hardness awaits data.  