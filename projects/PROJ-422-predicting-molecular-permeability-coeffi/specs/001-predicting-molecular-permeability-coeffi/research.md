# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We assess whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting **experimental permeability coefficients** of polymeric membranes. The target **must be an independent experimental measurement**; surrogate targets are allowed only when they are derived from validated simulation studies that do not use the same descriptor set, preserving construct validity (Constitution VII).

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

**Target Availability**: None of the verified datasets contain an experimental `permeability` column. The pipeline therefore proceeds as follows:

1. **Search for surrogate columns** that are documented as high‑quality simulation‑derived permeability values (e.g., `simulated_permeability`, `logS`, `solubility`).  
2. If such a surrogate is found, it is recorded as `target_type: "surrogate"` and used for modeling, with a clear note in the metadata that the target is surrogate.  
3. If **neither** experimental nor approved surrogate target exists, the pipeline **halts** and automatically opens a GitHub issue titled “Request open permeability dataset for PROJ‑422”. This satisfies FR‑001 while being transparent about data limitations.

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
- **MPNN (GNN)**: 3 message‑passing layers, hidden = 64, global mean pooling, regression head. Trained with Adam (`lr=0.001`), batch size = 32, early stopping (patience = 5) on validation loss. CPU‑only (`device="cpu"`). Checkpoint saved as `code/models/gnn.pt`.  
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`, trained on the full descriptor vector **plus** polymer‑type one‑hot features. Model serialized to `code/models/rf.pkl`.  

### 3.3 Training & Evaluation (only when a target exists)
- **Split**: 5‑fold stratified CV (when `polymer_type` exists) plus a hold‑out test set (rows with non‑null `target`). Splits are stored under `data/processed/` with both Parquet and CSV versions.  
- **Power Analysis**: Using `statsmodels.stats.power.TTestPower` with a conservative small effect (Cohen’s d = 0.3) at α = 0.05, 80 % power. Record `planned_sample_size`, `achieved_power`, and `sufficient` flag in `results/training_log.json`. **If `sufficient` is false, the training phase aborts** and logs the insufficiency.  
- **Metrics**: RMSE, MAE, R² on each CV fold and on the **hold‑out test set**; aggregate mean ± SD across folds.  
- **Statistical Test** (performed on the hold‑out set only): <br>1. Compute **per‑sample prediction errors** for GNN and RF on the **hold‑out test set** (not aggregated fold means).<br>2. Shapiro‑Wilk test on the paired error differences.<br>3. If normal (p ≥ 0.05) → paired t‑test; else → Wilcoxon signed‑rank test.<br>4. Record method, p‑value, `significant` flag (SC‑001, SC‑002).  
- **Bias Check**: <br>1. Compute Pearson correlation between the target and each descriptor.<br>2. If any |r| > 0.6, **drop those descriptors**, **re‑train** both models, and set `is_confounded: true`, `bias_warning: true`, and record the dropped descriptor list in `results/metrics.json`.  

All timings (wall‑clock hours) are logged in `results/training_log.json` (validated against `contracts/training_log.schema.yaml`).

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the final descriptor set → ranked CSV + bar‑chart PNG.  
- **GNNExplainer**: Run on a representative set of random test molecules; aggregate masks to a global subgraph importance ranking expressed as SMARTS strings; visualized as heatmaps.  
- **Cross‑Model Comparison**: **Deterministic overlap metric**: <br>1. Use a **pre‑defined deterministic lookup table** mapping each standard descriptor to a representative SMARTS pattern (e.g., `logP` ↔ aromatic ring SMARTS, `TPSA` ↔ polar‑oxygen SMARTS, `HBA` ↔ hydrogen‑bond‑acceptor SMARTS, etc.).<br>2. For the top‑5 GNN SMARTS, check whether they correspond to any of the top‑5 descriptor SMARTS via this lookup.<br>3. Compute the observed overlap count.<br>4. Generate a **null distribution** by randomly permuting descriptor rankings 10 000 times; compute a permutation‑test p‑value.<br>5. Store `overlap_top5`, `overlap_p_value`, and `overlap_significant` (p < 0.05) in `results/metrics.json`, satisfying SC‑003. This algorithmic mapping is independent of the SHAP results, and the permutation test demonstrates that the observed overlap is non‑trivial.  

## 4. Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No experimental permeability data | Phase 0 now also searches for **approved surrogate** columns; if none found, the pipeline halts and opens a GitHub issue. |
| Small dataset → overfitting | Early stopping, modest hidden size, dropout = 0.1, RF baseline; CV maximizes data usage. |
| Invalid SMILES | RDKit parsing guard; log & drop; retention guard ensures ≥ 95 % valid molecules. |
| High descriptor‑target correlation | Bias check now **drops** highly correlated descriptors and retrains before evaluation. |
| CPU memory overflow | Streaming load, batch size = 32, fallback to random subset if needed. |

### Decision / Rationale (Research.md)
- **CPU‑first**: All libraries (RDKit, PyTorch‑Geometric) have functional CPU implementations; dataset size (< 1 GB) fits comfortably within the runner’s RAM budget. No GPU is required, satisfying the compute feasibility constraints.  

---



