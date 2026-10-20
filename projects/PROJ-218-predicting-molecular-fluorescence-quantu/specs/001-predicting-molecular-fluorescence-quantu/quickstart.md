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
# Download the verified joint SMILES + FQY dataset (FluorDB v1.0)
python -m src.data.download_fluordb \
  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/fluordb.parquet \
  --output data/raw/joint.parquet

# The script automatically computes and records a SHA‑based checksum in `data/checksums.txt`.
# If the checksum does not match, the run aborts with an informative error.
```

*If you already have a local copy of the dataset, place it at `data/raw/joint.parquet` (or `joint.csv`). The pipeline will verify the checksum before proceeding.*

## 3️⃣ Pre‑processing (Deterministic Join, Clipping, Scaling & Feature Extraction)
```bash
python -m src.preprocessing.run \
  --joint data/raw/joint.parquet \
  --output data/processed/dataset.csv \
  --split-output data/processed/split.json
```
- Invalid SMILES are excluded and logged (FR‑009).  
- Boundary FQY values (exact 0 or 1) are **ε‑clipped** to `[1e-6, 1‑1e-6]` and logged (FR‑011).  
- **No additional min‑max scaling is performed; `fqy_norm` now contains the clipped values only** (FR‑010).  
- **Scaffold split** (80/10/10) is performed; overlap statistics are written to `split.json` (FR‑014).  
- If the resulting test set contains fewer than **20** molecules, a **warning** is logged (FR‑013) but the split ratios remain unchanged.  
- Solvent, temperature, and measurement‑method metadata are retained in the `metadata` column for downstream use (FR‑015).

## 4️⃣ Model Training
```bash
# Train the lightweight GNN (CPU‑only, max 50 epochs)
python -m src.training.train_gnn \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --epochs 50 \
  --patience 10 \
  --output models/gnn_best.pt

# Train the linear‑regression baseline on ECFP4 fingerprints + condition covariates
python -m src.training.train_lr \
  --data data/processed/dataset.csv \
  --split data/processed/split.json \
  --output models/lr.pkl
```
- Early stopping saves the checkpoint with the lowest validation loss (see FR).  
- Condition covariates (solvent, temperature, measurement method) are automatically incorporated into the model architectures (addresses methodology‑cf615953).

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
- Produces R², RMSE, and MAE for both models (FR‑005).  
- Generates parity plot and training‑loss curve (FR‑reference).  
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
- **Unseen atom/bond types** are encoded as zero‑vectors, a warning is logged and the molecule is **processed** for test‑set evaluation (FR‑012‑b).  
- **For new inference inputs** the script will **log a warning and skip** the molecule (FR‑012‑a).  
- Atom attributions are aggregated into contiguous aromatic or conjugated fragments, producing the top‑ranked substructures.  
- A **sanity‑check** runs SHAP on a random subset of 10 molecules and requires Pearson correlation ≥ 0.7 between IG and SHAP scores to confirm attribution reliability (addresses methodology‑8d1fbe71).  
- The aggregation step is noted as an approximate proxy for substructure importance.

## 7️⃣ Attribution Validation
```bash
python -m src.interpretability.validate_attributions \
  --attribution-dir attributions/ \
  --reference-motifs data/reference/fluorophore_motifs.csv \
  --output results/attribution_validation.json
```
- The reference motif list is **pruned of any motifs that appear in the training set**, guaranteeing independence (addresses scientific_soundness‑1bfb68ae).  
- Computes overlap of the top‑20 substructures with the **pruned** reference set; requires **≥ 12 matches** (≥ 60 %).  
- Performs a **permutation test**: attribution scores are shuffled among all fragments 100 times, top‑20 sets recomputed, and the mean random overlap recorded. The observed overlap must be **> 1.5×** this mean (SC‑005). No p‑value requirement is imposed (aligns with SC‑005).  
- **Spot‑check**: selects the single test molecule with the highest experimental FQY; its top‑5 substructures must include at least **3** motifs from the reference set (matches US‑3 Scenario 3).

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



