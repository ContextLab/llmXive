# Quickstart: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

This guide walks a new researcher through the entire end‑to‑end pipeline on the free‑tier GitHub Actions runner (or locally on a similar Linux environment).

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
# Download the joint FluorDB v1.0 dataset
python -m src.data.download_fluordb \
  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet \
  --output data/raw/fluordb.parquet
```
- The script computes a SHA‑256 checksum (recorded in `data/checksums.txt`) to ensure data integrity.

## 3️⃣ Deterministic Cleaning & Scaffold Split
```bash
# Clean the raw dataset (remove invalid SMILES, ε‑clip boundary FQY values, extract metadata)
python -m src.preprocessing.clean \
  --input data/raw/fluordb.parquet \
  --output data/processed/cleaned.parquet

# Perform scaffold‑based 80/10/10 split; enforce a minimum **50** test molecules
python -m src.preprocessing.scaffold_split \
  --input data/processed/cleaned.parquet \
  --output-dir data/processed/split/ \
  --min-test-size 50
```
- Invalid SMILES are **excluded** and logged (FR‑009).  
- Exact 0 or 1 FQY values are **ε‑clipped** to `[1e-6, 1‑1e-6]` and logged (FR‑011).  
- No additional scaling is performed (FR‑010).  
- Scaffold split guarantees zero overlap; counts and overlap stats are written to `split_stats.json` (FR‑014).  
- The script **aborts** if the test set contains fewer than **50** molecules (FR‑013).

## 4️⃣ Feature Extraction
```bash
# Node/edge features for GNN
python -m src.features.rdkit_features \
  --input data/processed/split/train.parquet \
  --output data/processed/features/train_graphs.pt

# ECFP4 fingerprints for baseline
python -m src.features.ecfp4 \
  --input data/processed/split/train.parquet \
  --output data/processed/features/train_ecfp4.npy
```
- Node features: atom type, hybridization, formal charge.  
- Edge features: bond type, conjugation status (FR‑001).  
- Condition covariates (solvent, temperature, measurement method) are automatically appended (FR‑015).

## 5️⃣ Model Training
```bash
# Train the lightweight GNN (CPU‑only, max 50 epochs, early stopping patience=10)
python -m src.training.train \
  --graph-features data/processed/features/train_graphs.pt \
  --targets data/processed/split/train.parquet \
  --validation-split data/processed/split/validation.parquet \
  --epochs 50 \
  --patience 10 \
  --output models/gnn_best.pt

# Train the linear‑regression baseline on ECFP4 + covariates
python -m src.training.train_lr \
  --features data/processed/features/train_ecfp4.npy \
  --metadata data/processed/split/train.parquet \
  --output models/lr.pkl
```
- Early stopping saves the checkpoint with the lowest validation loss (FR‑004).  
- Condition covariates are concatenated to the input vectors (methodology‑cf615953).

## 6️⃣ Evaluation
```bash
python -m src.evaluation.evaluate \
  --gnn-model models/gnn_best.pt \
  --lr-model models/lr.pkl \
  --test-data data/processed/split/test.parquet \
  --output results/metrics.json \
  --fig-dir figures/
```
- Computes R², RMSE, MAE for both models (FR‑005).  
- Generates a parity plot, training‑loss curve, and condition‑wise metric tables (FR‑007).  
- Bootstrap confidence interval for R² is computed; results are stored in `results/metrics.json`.  
- Unseen atom/bond types encountered in the test set are **logged**; they are retained for evaluation, while any new inference inputs with unseen chemistry will be **skipped** with a warning (FR‑012).

## 7️⃣ Interpretability (Integrated Gradients & SHAP)
```bash
# Integrated Gradients (primary) on the whole test set
python -m src.interpretability.integrated_gradients \
  --model models/gnn_best.pt \
  --test-data data/processed/split/test.parquet \
  --output attributions/ig/

# SHAP sanity‑check on a random subset of **100** test molecules, three seeds
python -m src.interpretability.shap_sanity \
  --model models/gnn_best.pt \
  --test-data data/processed/split/test.parquet \
  --sample-size 100 \
  --seeds 42 123 999 \
  --output attributions/shap/
```
- IG produces atom‑level attribution scores saved as JSON per molecule.  
- SHAP scores are compared to IG; the script **records** Pearson correlation and its 95 % confidence interval (methodology‑3e88f02e) but does **not abort** if the correlation falls below 0.7.

## 8️⃣ Substructure Aggregation & Validation
```bash
# Aggregate atom attributions into aromatic/conjugated fragments and rank the top‑N fragments.
python -m src.interpretability.aggregate_substructures \
  --ig-dir attributions/ig/ \
  --output attributions/aggregated_top20.json

# Also produce an atom‑level top‑ranked list for completeness
python -m src.interpretability.aggregate_substructures \
  --ig-dir attributions/ig/ \
  --atom-level \
  --output attributions/atom_top20.json

# Validate against the curated fluorophore‑motif reference set (full set, no pruning)
python -m src.interpretability.validate_attributions \
  --aggregated attributions/aggregated_top20.json \
  --reference data/reference/fluorophore_motifs.csv \
  --train-data data/processed/split/train.parquet \
  --test-data data/processed/split/test.parquet \
  --output results/attribution_validation.json
```
- The validation script computes **overlap count**, **enrichment factor**, and a **hypergeometric p‑value** against 100 random draws; it also spot‑checks the highest‑FQY test molecule and reports whether ≥ 3 of its top‑5 fragments match the reference set (US‑3 Scenario 3). No hard pass/fail gate is imposed.

## 9️⃣ Covariate Impact Analysis
```bash
# Train/evaluate GNN and baseline **with** covariates (default) and **without** them
python -m src.evaluation.covariate_ablation \
  --gnn-model models/gnn_best.pt \
  --lr-model models/lr.pkl \
  --train-data data/processed/split/train.parquet \
  --validation-data data/processed/split/validation.parquet \
  --test-data data/processed/split/test.parquet \
  --output results/covariate_impact.json
```
- Produces ΔR², ΔRMSE, and Pearson correlations between each covariate and model residuals, allowing assessment of potential confounding.

## 🔟 Final Report Generation
```bash
python -m src.reporting.generate_report \
  --metrics results/metrics.json \
  --attribution-validation results/attribution_validation.json \
  --covariate-impact results/covariate_impact.json \
  --fig-dir figures/ \
  --output report/
```
- Populates `report/` with markdown tables, figures, and a `manifest.json` that the downstream paper stage will consume.

## 🔧 Clean‑up (optional)
```bash
# Remove large raw files to stay within CI disk quota
rm -rf data/raw/
```

**All steps are fully scripted; re‑running the `quickstart.sh` script reproduces the entire analysis from raw download to final report without manual intervention.**