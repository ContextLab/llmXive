# Quickstart: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

This guide walks a new researcher through the entire end‑to‑end pipeline on the free‑tier GitHub Actions runner (or locally on a similar Linux environment).

## 1️⃣ Prerequisites
```bash
# Clone the repository (already provided in the CI environment)
git clone <repo‑url>
cd quantum-yield-gnn

# Create a clean virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2️⃣ Data Download & Verification
```bash
# NOTE: No open, verified dataset provides both SMILES and experimental FQY.
# You must supply a **public joint file** containing SMILES and FQY.
# Place it at `data/raw/joint.parquet` (or `data/raw/joint.csv`).
# The file must contain at least 200 molecules.
# The pipeline will abort with an informative error if this requirement is not met.

# If you have a separate SMILES‑only file, you can download it (verified source):
python -m src.data.download_smiles \
  --url https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet \
  --output data/raw/smiles.parquet
```

*The download scripts automatically compute and record SHA checksums in `data/checksums.txt`. If a checksum mismatch occurs, the run stops.*

## 3️⃣ Pre‑processing (Deterministic Join, Clipping, Scaling & Feature Extraction)
```bash
# Join SMILES and FQY via InChIKey (the joint file already contains both columns).
# This step also clips boundary values and performs the scaffold split.
python -m src.preprocessing.run \
  --joint data/raw/joint.parquet \
  --output data/processed/dataset.csv \
  --split-output data/processed/split.json
```
- Invalid SMILES are excluded and logged (FR‑009).  
- Boundary FQY values (exact 0 or 1) are clipped to `[1e-6, 1‑1e-6]` and logged (FR‑011).  
- **No additional min‑max scaling is performed; `fqy_norm` now contains the clipped values only (FR‑010 update).**  
- Scaffold split (80/10/10) is logged; overlap statistics are written to `split.json` (FR‑014).  
- If fewer than 200 molecules are present in the joint file, the script aborts with a clear error.

## 4️⃣ Model Training
```bash
# Train the lightweight GNN (CPU‑only, max 50 epochs)
python -m src.training.train_gnn \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --epochs 50 \
  --patience 10 \
  --output models/gnn_best.pt

# Train the linear‑regression baseline on ECFP4 fingerprints
python -m src.training.train_lr \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --output models/lr.pkl
```
- Early stopping saves the checkpoint with the lowest validation loss (FR‑004).  
- Convergence metrics are logged for later plotting (FR‑007).

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
- Generates parity plot and training‑loss curve (FR‑007).  
- If solvent/temperature metadata are present, stratified metrics are added (FR‑017).  
- All numbers and figures become the **single source of truth** for the paper (Constitution Check).

## 6️⃣ Interpretability
```bash
python -m src.interpretability.compute_attributions \
  --model models/gnn_best.pt \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --method integrated_gradients \
  --top-k 20 \
  --output attributions/
```
- Outputs per‑molecule JSON files containing atom‑level Integrated Gradients scores.  
- Unseen atom or bond types trigger a warning and the molecule is skipped (FR‑012).  
- Atom attributions are aggregated into contiguous aromatic or conjugated fragments, producing the top‑ranked substructures (FR‑006).

## 7️⃣ Attribution Validation
```bash
python -m src.interpretability.validate_attributions \
  --attribution-dir attributions/ \
  --reference-motifs data/reference/fluorophore_motifs.csv \
  --output results/attribution_validation.json
```
- Checks that the reference motif list is **independent** of training/test molecules (scientific‑soundness‑68e86578).  
- Computes overlap with the curated motif list (≥ 12 of 20) and enrichment > 1.5× random baseline (SC‑005).  
- Performs the spot‑check on the five highest‑FQY test molecules (≥ 3 matching motifs).  

## 8️⃣ Final Report Generation
```bash
python -m src.reporting.generate_report \
  --metrics results/metrics.json \
  --attribution-validation results/attribution_validation.json \
  --fig-dir figures/ \
  --output report/
```
- Populates `report/` with markdown tables, figures, and a `manifest.json` that the downstream paper stage will consume.

## 9️⃣ Clean‑up (optional)
```bash
# Remove large raw files to stay within CI disk quota
rm -rf data/raw/
```

**All steps are fully scripted; re‑running the `quickstart.sh` script reproduces the entire analysis from raw download to final report.**  

---



