# Quickstart: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

This guide walks a new researcher through the entire end‑to‑end pipeline on the free‑tier GitHub Actions runner (or locally on a similar Linux environment).

## 1️⃣ Prerequisites
```bash
# Clone the repository (already provided in the CI environment)
git clone 
cd quantum-yield-gnn

# Create a clean virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2️⃣ Data Download & Verification
```bash
# SMILES dataset (parquet)
python -m src.data.download_smiles \
  --url https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet \
  --output data/raw/smiles.parquet

# FQY dataset (JSON)
python -m src.data.download_fqy \
  --url https://doi.org/10.48700/datst.mff4d-q4a24 \
  --output data/raw/fqy.json

# Verify checksums (automatically done by the scripts)
```

*If a joint SMILES‑FQY file is not available, the pipeline will stop here with a clear error message (see `plan.md`). Provide a combined dataset before proceeding.*

## 3️⃣ Pre‑processing
```bash
# Parse SMILES, generate graph features, join with FQY via InChIKey, clip boundaries, normalize, capture metadata, and scaffold‑split
python -m src.preprocessing.run \
  --smiles data/raw/smiles.parquet \
  --fqy data/raw/fqy.json \
  --output data/processed/dataset.csv \
  --split-output data/processed/split.json
```
- Logs invalid SMILES (FR‑009).  
- Logs any boundary FQY clipping (FR‑011).  
- Captures solvent, temperature, and measurement‑method metadata (FR‑015).  
- Generates `dataset.csv` adhering to `contracts/processed_dataset.schema.yaml`.  
- Generates `split.json` containing scaffold split metadata (logged for FR‑014).  
- **If fewer than 200 molecules are successfully joined, the script aborts with an informative error** (see Join Validation in `plan.md`).

## 4️⃣ Model Training
```bash
# Train GNN (CPU‑only, max 50 epochs)
python -m src.training.train_gnn \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --epochs 50 \
  --patience 10 \
  --output models/gnn_best.pt

# Train linear regression baseline on ECFP4
python -m src.training.train_lr \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --output models/lr.pkl
```
- Early stopping saves the best checkpoint (FR‑004).  
- Training logs convergence metrics (FR‑007).

## 5️⃣ Evaluation
```bash
python -m src.evaluation.evaluate \
  --gnn-model models/gnn_best.pt \
  --lr-model models/lr.pkl \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --output results/metrics.json \
  --fig-dir figures/
```
- Produces R², RMSE, MAE for both models (FR‑005).  
- Generates parity plot and convergence plot (FR‑007).  
- Stratifies metrics by solvent/temperature if metadata present (FR‑017).  
- **All numbers and figures are the Single Source of Truth for the paper** (see Constitution Check in `plan.md`).

## 6️⃣ Interpretability
```bash
python -m src.interpretability.compute_attributions \
  --model models/gnn_best.pt \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --top-k 20 \
  --method integrated_gradients \
  --output attributions/
```
- Outputs one JSON per molecule adhering to `contracts/processed_dataset.schema.yaml` plus attribution fields.  
- Aggregates atom‑level attributions into aromatic/conjugated substructures (FR‑006).  
- Detects unseen atom/bond types during inference, logs warnings, and skips those molecules (FR‑012).

## 7️⃣ Attribution Validation
```bash
python -m src.interpretability.validate_attributions \
  --attribution-dir attributions/ \
  --reference-motifs data/reference/fluorophore_motifs.csv \
  --output results/attribution_validation.json
```
- Checks independence of the reference motif list from training/test molecules (scientific soundness‑78b9e565).  
- Computes overlap with the curated reference set (≥ 12 of 20) and enrichment > 1.5× random baseline (SC‑005).  
- Performs the 100‑draw random baseline as defined in `research.md`.

## 8️⃣ Final Report Generation
```bash
python -m src.reporting.generate_report \
  --metrics results/metrics.json \
  --attribution-validation results/attribution_validation.json \
  --fig-dir figures/ \
  --output report/
```
- Populates `report/` with markdown tables, figures, and a `manifest.json` that the paper‑stage will consume.

## 9️⃣ Clean‑up (optional)
```bash
# Remove intermediate large files to stay within CI disk quota
rm -rf data/raw/
```

**All steps are fully scripted; re‑running the `quickstart.sh` script reproduces the entire analysis from raw download to final report.**  

---

