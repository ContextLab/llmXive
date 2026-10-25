# Quickstart: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

This guide walks a new researcher through the **executable portion** of the pipeline (data download, cleaning, scaffold split, graph feature extraction, model training, evaluation, attribution, and reporting) on the free‑tier GitHub Actions runner (or locally on a similar Linux environment).

## 1️⃣ Prerequisites
```bash
# Clone the repository (already present in the CI environment)
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
# Download the verified joint SMILES + FQY dataset
python -m src.data.download_fluordb \
  --url https://huggingface.co/datasets/fluordb/v1 \
  --output data/raw/fluordb.parquet
```
- The script computes a SHA‑256 checksum (recorded in `data/checksums.txt`) to guarantee integrity (FR‑018).

## 3️⃣ Deterministic Cleaning & Metadata Extraction
```bash
# Clean the raw file: remove invalid SMILES, ε‑clip FQY, extract solvent/temperature/method metadata.
python -m src.preprocessing.clean \
  --input data/raw/fluordb.parquet \
  --output data/processed/cleaned.parquet
```
- Invalid SMILES are **excluded** and logged (FR‑009).  
- FQY values are clipped to the interval (ε, 1‑ε) with ε = 1e‑6 (FR‑010).  
- Any boundary values (exact 0 or 1) are logged (FR‑011).  
- Optional columns `solvent`, `temperature`, `measurement_method` are copied into a nested `metadata` field (FR‑015).

## 4️⃣ Scaffold‑Based Split (80/10/10, min test = 50)
```bash
python -m src.preprocessing.scaffold_split \
  --input data/processed/cleaned.parquet \
  --output-dir data/processed/split/ \
  --min-test-size 50
```
- Murcko scaffolds are extracted, and the dataset is partitioned ensuring **zero scaffold overlap** between train and test (FR‑002, FR‑014).  
- If the test set ends up smaller than a minimal acceptable size after five reseed attempts, the script aborts with a warning (FR‑013)..  
- Split statistics are written to `data/processed/split/split_stats.json`.

## 5️⃣ Graph Feature Extraction (RDKit)
```bash
python -m src.features.rdkit_features \
  --input data/processed/split/train.parquet \
  --output data/processed/features/train_graphs.pt

python -m src.features.rdkit_features \
  --input data/processed/split/validation.parquet \
  --output data/processed/features/val_graphs.pt

python -m src.features.rdkit_features \
  --input data/processed/split/test.parquet \
  --output data/processed/features/test_graphs.pt
```
- Node features: atom type, hybridization, formal charge.  
- Edge features: bond type, conjugation status (FR‑001).  
- Any molecule containing an atom or bond type unseen in the training set triggers a **warning** and is **skipped for inference** (FR‑012); such molecules are retained for evaluation.

## 6️⃣ Model Training & Baseline Comparison
```bash
# Train the GNN (≤ 5 M parameters) with early stopping
python -m src.training.train \
  --train data/processed/features/train_graphs.pt \
  --val data/processed/features/val_graphs.pt \
  --output-dir models/gnn/ \
  --max-epochs 50 \
  --patience 10

# Train the linear regression baseline on ECFP4 fingerprints
python -m src.models.linear_regression \
  --train data/processed/features/train_graphs.pt \
  --val data/processed/features/val_graphs.pt \
  --output models/baseline.pkl
```
- Training completes without GPU usage; the best checkpoint is saved based on validation loss (FR‑004).  
- Early stopping saves the epoch with the lowest validation loss if convergence fails (FR‑004).

## 7️⃣ Evaluation
```bash
python -m src.evaluation.evaluate \
  --model models/gnn/model_best.pt \
  --baseline models/baseline.pkl \
  --test data/processed/features/test_graphs.pt \
  --output metrics.json
```
- Outputs R², RMSE, and MAE for both the GNN and the baseline (FR‑005).  
- SC‑001 records the GNN vs. baseline R² improvement.

## 8️⃣ Feature Attribution & Interpretability
```bash
# Integrated Gradients
python -m src.interpretability.integrated_gradients \
  --model models/gnn/model_best.pt \
  --test data/processed/features/test_graphs.pt \
  --output attributions/ig.npy

# SHAP explanations
python -m src.interpretability.shap_explain \
  --model models/gnn/model_best.pt \
  --test data/processed/features/test_graphs.pt \
  --output attributions/shap.npy

# Aggregate atom‑level attributions into chemically meaningful substructures
python -m src.interpretability.aggregate_substructures \
  --ig attributions/ig.npy \
  --shap attributions/shap.npy \
  --reference data/reference/fluorophore_motifs.csv \
  --output attribution_metrics.json
```
- Produces a ranked list of the **top 20 substructures** (FR‑006).  
- SC‑005 reports overlap with the curated motif set and enrichment vs random baseline.  
- SC‑006 reports Pearson correlation between IG and SHAP scores on ≥ 30 randomly selected test molecules.

## 9️⃣ Reporting
```bash
python -m src.reporting.generate_report \
  --metrics metrics.json \
  --attribution attribution_metrics.json \
  --split-stats data/processed/split/split_stats.json \
  --output-dir reports/
```
- Generates training convergence plot, parity plot, feature‑importance bar chart, and a JSON manifest.  
- The `reports/` folder is archived as a CI artifact (SC‑007).

## 🔟 Resource Monitoring & Logging
All scripts import `src.utils.logger` which records:
- Wall‑clock time (must stay ≤ 6 h) – SC‑002.  
- Peak RAM usage (must stay ≤ 7 GB) – SC‑003.  
- Counts of excluded SMILES, scaffold overlap statistics, clipping warnings, and any unseen atom/bond warnings.

## 11️⃣ Clean‑up (optional)
```bash
# Remove large raw files to stay within CI disk quota
rm -rf data/raw/
```

**All steps are fully scripted; re‑running the `quickstart.sh` script reproduces the entire analysis from raw download to final report without manual intervention.** When a new joint dataset becomes available, simply update the URL in `download_fluordb.py` and re‑run the pipeline.

---



