# Quickstart: Predicting Material Properties from Compositional Data

This guide shows how to run the full composition‑only pipeline on a fresh GitHub Actions (or local) runner.

## 1️⃣ Prerequisites
- Python 3.11
- Git (to clone the repository)
- Internet access (to download the open Materials Project parquet file)

## 2️⃣ Clone the repository
```bash
git clone https://github.com/your-org/PROJ-033-predicting-material-properties-from-comp.git
cd PROJ-033-predicting-material-properties-from-comp
```

## 3️⃣ Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
*`requirements.txt` pins the exact versions listed in `plan.md`.*

## 4️⃣ Download the dataset
The script will automatically stream the open Materials Project data; no manual download is needed.
```bash
python src/utils/data_loader.py --stream
```
This will:
- Pull the verified parquet file from HuggingFace.
- Verify its SHA‑256 checksum and write it to `data/raw/`.
- Produce `data/processed/materials_processed.csv`.

## 5️⃣ Train the composition‑only GNN
```bash
python src/training/train_gnn.py \
    --config configs/train_config.yaml \
    --seed 42
```
Key arguments:
- `--config` points to a YAML with hyper‑parameters (layers, hidden dim, etc.).
- The script respects the 30‑minute per‑epoch and 6‑hour total runtime guards.

## 6️⃣ Evaluate & generate reports
```bash
python src/training/evaluate.py \
    --model_path outputs/gnn_checkpoint_<hash>.pt \
    --metrics_out data/results_composition_only.json
python src/interpret/pca_correlation.py \
    --embeddings_path outputs/node_embeddings.npy \
    --report_out interpretability_report.md
python src/training/aggregate_system_metrics.py \
    --metrics_in data/results_composition_only.json \
    --out_csv data/metrics_by_system.csv
```

## 7️⃣ Prediction intervals
When running inference on new formulas, the script computes residuals on the validation fold, estimates σ̂, and returns a [deferred] prediction interval as:

```
prediction ± 1.96 * σ̂
```

## 8️⃣ Inspect the outputs
- **Metrics**: `data/results_composition_only.json` (validated against `contracts/model_metrics.schema.yaml`).  
- **Per‑system metrics**: `data/metrics_by_system.csv`.  
- **Interpretability**: `interpretability_report.md`.  

## 9️⃣ Run the test suite
```bash
pytest -q tests/
```
All contract tests should pass, confirming schema compliance.

## 🔟 Clean up (optional)
```bash
rm -rf data/raw/*  # removes a substantial amount of parquet files
```

**That’s it!** The pipeline is fully reproducible and runs entirely on CPU within the CI limits.

---


