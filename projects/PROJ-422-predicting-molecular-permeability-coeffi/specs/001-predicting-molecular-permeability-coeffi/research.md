# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We assess whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting **experimental permeability coefficients** of polymeric membranes. The target **must be an independent experimental measurement**; surrogate targets are allowed only when they are derived from **validated simulation studies** and pass an **independence verification** (max |r| < 0.5 with all standard descriptors) to preserve construct validity per Constitution VII.

## 2. Dataset Strategy

### 2.1 Verified Open Datasets
Only the following open datasets (verified URLs) are programmatically accessible via the Hugging Face `datasets` library:

| Dataset | URL | Format | Variables |
|---------|-----|--------|-----------|
| SMILES‑Transformers | https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet | Parquet | `smiles` |
| SELFormer‑smiles | https://huggingface.co/datasets/HUBioDataLab/SELFormer-smiles/resolve/main/data.csv | CSV | `smiles` |
| RDKit‑chemical | https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet | Parquet | `smiles`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds` |
| ChEMBL‑2025‑RDKit (randomized) | https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet | Parquet | same as above |
| Half‑ChEMBL‑2025‑RDKit | https://huggingface.co/datasets/fabikru/half-of-chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet | Parquet | same as above |
| TPSA / GRAPO | https://huggingface.co/datasets/Alan123/hba_hbd_tpsa_grpo/resolve/main/data/train-00000-of-00001.parquet | Parquet | `smiles`, `tpsa`, `hba`, `hbd` |

**Target Availability**: None of the verified datasets contain an experimental `permeability` column, nor an approved surrogate column (e.g., `simulated_permeability`, `logS`). Consequently:

1. **Phase 0** of the pipeline searches for these columns.  
2. **If none are found**, the pipeline **halts** after logging a clear error and **automatically opens a GitHub issue** titled “Request open permeability dataset for PROJ‑422”.  
3. **If a surrogate target is found**, the pipeline performs a **surrogate‑independence verification**: compute Pearson correlation between the surrogate and every standard descriptor; accept the surrogate only when max |r| < 0.5. This guarantees the surrogate is not a deterministic function of the descriptors, preserving validation independence.

Thus, the research proceeds only when a suitable target is available; otherwise the pipeline stops transparently, satisfying FR‑001 while respecting the data limitation.

### 2.2 Data Volume & Streaming
All listed datasets are ≤ 1 GB. We will load them with `datasets.load_dataset(..., streaming=True)` to keep RAM usage low while processing the full data.

## 3. Methodology

### 3.1 Feature Engineering
1. **SMILES → Graph** using `rdkit.Chem.MolFromSmiles`. Invalid SMILES are logged and excluded (FR‑011).  
2. **Node Features**: atomic number, degree, formal charge, hybridization, aromatic flag.  
3. **Edge Features**: bond type, conjugation flag.  
4. **Standard Descriptors** (RDKit): MW, TPSA, H‑bond acceptors/donors, rotatable bonds, logP.  
5. **Polymer‑type One‑Hot** (if present) added for both models.  

All transformations output `data/processed/processed_data.parquet` **and** `processed_data.csv`, conforming to `contracts/dataset.schema.yaml`.

### 3.2 Model Architectures
- **MPNN (GNN)**: 3‑layer MPNN, hidden = 64, global mean pooling, regression head. Trained with Adam (`lr=0.001`), batch size = 32, early stopping (patience = 5) on validation loss. CPU‑only (`device="cpu"`). Checkpoint saved as `code/models/gnn.pt`.  
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`, trained on the full descriptor vector **plus** polymer‑type one‑hot features. Model serialized to `code/models/rf.pkl`.  

### 3.3 Training & Evaluation (only when a target exists)
- **Split**: 5‑fold stratified CV (when `polymer_type` exists) plus a hold‑out test set (rows with non‑null `target`). Splits are stored under `data/processed/` with both Parquet and CSV versions.  
- **Power Analysis**: Using `statsmodels.stats.power.TTestPower` with a conservative small effect (Cohen’s d = 0.3) at α = 0.05, 80 % power. Record `planned_sample_size`, `achieved_power`, and `sufficient` flag in `results/training_log.json`. **If `sufficient` is false, the training phase aborts** and logs the insufficiency (FR‑015).  
- **Metrics**: RMSE, MAE, R² on each CV fold and on the **hold‑out test set** (not aggregated fold means); aggregate mean ± SD across folds.  
- **Statistical Test** (performed on the hold‑out set only): <br>1. Compute **per‑sample prediction errors** for GNN and RF on the **hold‑out test set** (not aggregated fold means).<br>2. Shapiro‑Wilk test on the paired error differences.<br>3. If normal (p ≥ 0.05) → paired t‑test; else → Wilcoxon signed‑rank test.<br>4. Record method, p‑value, `significant` flag (SC‑001, SC‑002).  
- **Post‑split Confounding Assessment**: <br>1. Compute Pearson correlation between each descriptor and the target **using only the training folds**.<br>2. Record the **maximum absolute correlation** as `correlation_coefficient`. <br>3. Set `is_confounded: true` and `bias_warning: true` if max |r| > 0.6. **No descriptors are removed**, avoiding data leakage.  

All timings (wall‑clock hours) are logged in `results/training_log.json` (validated against `contracts/training_log.schema.yaml`).

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the final descriptor set → ranked CSV + bar‑chart PNG.  
- **GNNExplainer**: Run on a representative set of random test molecules; aggregate masks to a global subgraph importance ranking expressed as SMARTS strings; visualized as heatmaps.  
- **Empirical Overlap Metric**: <br>1. For each standard descriptor, compute Pearson correlation with the frequency of each SMARTS substructure across the **training set**.<br>2. Define a **data‑driven mapping** by selecting, for each descriptor, the SMARTS with the highest correlation.<br>3. For the top‑5 GNN SMARTS, check correspondence to the top‑5 descriptor‑mapped SMARTS.<br>4. Count overlaps (`overlap_top5`).<br>5. Set `overlap_meets_threshold` **true when `overlap_top5 ≥ 3`** (per SC‑003).<br>6. Store `overlap_top5` and `overlap_meets_threshold` in `results/metrics.json`.  

### 3.5 Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No experimental permeability data | Phase 0 now also searches for **approved surrogate** columns and validates independence (max |r| < 0.5). If none exist, the pipeline **halts** and **opens a GitHub issue**; no downstream analysis is fabricated. |
| Small dataset → overfitting | Early stopping, modest hidden size, dropout = 0.1, RF baseline; CV maximizes data usage. |
| Invalid SMILES | RDKit parsing guard; logs & drops invalid entries (FR‑011). |
| High descriptor‑target correlation | Post‑split confounding assessment records correlation but does **not** drop descriptors; flags potential confounding without inducing leakage. |
| CPU memory overflow | Streaming load, batch size = 32, fallback to random subset if needed. |

## 4. Decision / Rationale
- **CPU‑first**: All libraries (RDKit, PyTorch‑Geometric) have functional CPU implementations; dataset size (< 1 GB) fits comfortably within the runner’s RAM budget. No GPU is required, satisfying the compute feasibility constraints.

---



