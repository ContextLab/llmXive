# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We assess whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting **experimental permeability coefficients** of polymeric membranes. The target must be an independent experimental measurement; no surrogate target will be used unless a formal spec‑amendment approves a non‑descriptor surrogate (Constitution VII).

## 2. Dataset Strategy

### 2.1 Verified Open Datasets
Only the following open datasets (verified URLs) are available via the Hugging Face `datasets` library:

| Dataset | URL | Format | Variables |
|---------|-----|--------|-----------|
| **SMILES‑Transformers** | https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet | Parquet | `smiles` |
| **SELFormer‑smiles** | https://huggingface.co/datasets/HUBioDataLab/SELFormer-smiles/resolve/main/data.csv | CSV | `smiles` |
| **RDKit‑chemical** | https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet | Parquet | `smiles`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds` |
| **ChEMBL‑2025‑RDKit (randomized)** | https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet | Parquet | same as above |
| **Half‑ChEMBL‑2025‑RDKit** | https://huggingface.co/datasets/fabikru/half-of-chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet | Parquet | same as above |
| **TPSA / GRAPO** | https://huggingface.co/datasets/Alan123/hba_hbd_tpsa_grpo/resolve/main/data/train-00000-of-00001.parquet | Parquet | `smiles`, `tpsa`, `hba`, `hbd` |

**FATAL MISMATCH**: None of the verified datasets listed above contain experimental permeability coefficients. Consequently, the pipeline **MUST halt** in Phase 0. Proceeding with any of these datasets would violate FR‑001 and Constitution VII.

*Spec‑amendment path*: If stakeholders approve a surrogate target that is **not** one of the baseline descriptors (e.g., an experimentally measured diffusion coefficient from an open dataset), that column will be used as the regression target. The surrogate column will be **removed** from the descriptor set supplied to the Random Forest baseline to avoid circular validation (see Phase 2). Until such an amendment is approved or a new verified dataset is provided, no modeling will be performed.

### 2.2 Target Selection (Current Limitation)
- **If** a dataset with a true `permeability` column appears, it becomes the regression target.  
- **If** a surrogate target is approved via spec amendment, the chosen column (e.g., `diffusion_coeff`) will be used, and the pipeline will note its surrogate nature throughout.  
- **Otherwise**, the pipeline stops after preprocessing; no model training or downstream analysis occurs. **The production of dummy models or fabricated results to satisfy the pipeline is strictly prohibited.**

### 2.3 Data Volume & Streaming
All listed datasets are ≤ 1 GB. We will load them with `datasets.load_dataset(..., streaming=True)` to keep RAM usage low while processing the full dataset.

## 3. Methodology

### 3.1 Feature Engineering
1. **SMILES → Graph** using `rdkit.Chem.MolFromSmiles`. Invalid SMILES are logged and excluded (FR‑011).  
2. **Node Features**: atomic number, degree, formal charge, hybridization, aromatic flag.  
3. **Edge Features**: bond type, conjugation flag.  
4. **Standard Descriptors** (RDKit): MW, TPSA, H‑bond acceptors/donors, rotatable bonds, logP.  
5. **Polymer‑type One‑Hot** (if present) is added as a categorical feature for both models.  
6. **Graph‑Derived Statistics** (for potential ablation, not required) are computed but not used in the baseline.  

All transformations output `data/processed/processed_data.parquet` **and** `processed_data.csv`, conforming to `contracts/dataset.schema.yaml`.

### 3.2 Model Architectures
- **MPNN (GNN)**: 3 message‑passing layers, hidden = 64, global mean pooling, linear regression head. Trained with Adam (`lr=0.001`), batch size = 32, early stopping (patience = 5) on validation loss. CPU‑only (`device="cpu"`). Checkpoint saved as `code/models/gnn.pt`.  
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`, trained on the full descriptor vector **plus** polymer‑type one‑hot features. Model serialized to `code/models/rf.pkl`.  

### 3.3 Training & Evaluation (only when `target` is present or approved surrogate)
- **Split**: 5‑fold stratified cross‑validation (when `polymer_type` exists) plus a [deferred] hold‑out test set (only rows with non‑null `target` or approved surrogate). The splits are stored under `data/processed/` with both Parquet and CSV versions.
- **Power Analysis**: Using `statsmodels.stats.power.tt_ind_solve_power` with a conservative small effect (Cohen’s d = 0.3) at α = 0.05, 80 % power. Record planned sample size, achieved power, and flag insufficient power (SC‑004).  
- **Metrics**: RMSE, MAE, R² on each CV fold and on the hold‑out set; aggregate mean ± SD across folds.  
- **Statistical Test**:  
  1. Shapiro‑Wilk test on paired error differences.  
  2. If normal (p ≥ 0.05) → paired t‑test; else → Wilcoxon signed‑rank test.  
  3. Record method, p‑value, `significant` flag (SC‑001, SC‑002).  
- **Bias Check**: Compute Pearson correlation between the target and each descriptor. If any |r| > 0.6 set `is_confounded` = true and `bias_warning` = true; record the maximum |r| in results.  

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the descriptor baseline (excluding any surrogate target) → mean absolute SHAP values are ranked and plotted.  
- **GNNExplainer**: Run on a representative set of random test molecules; aggregate masks to a global subgraph importance ranking of functional groups/substructures; visualized as heatmaps.  
- **Cross‑Model Comparison**: Compute an **overlap‑count metric**: each top‑5 GNN‑identified substructure is mapped to the most chemically related descriptor (e.g., aromatic ring → logP). Count overlaps with the top‑5 SHAP‑ranked descriptors. Store integer `overlap_top5` and boolean `overlap_meets_threshold` (true if ≥ 3) in `results/metrics.json`, satisfying SC‑003.  

All outputs are saved under `results/interpretability/`.

## 4. Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No true permeability data | Phase 0 halts with explicit message and creates a GitHub issue; spec‑amendment path for surrogate target. |
| Small dataset → overfitting | Early stopping, modest hidden size, dropout = 0.1, RF baseline; cross‑validation maximizes data usage. |
| Invalid SMILES | RDKit parsing guard; log & drop; retention guard ensures ≥ 95 % valid molecules. |
| Surrogate target circularity | Surrogate column is removed from the descriptor set used by the RF baseline; GNN never sees the target as input. |
| High correlation between descriptors & surrogate target | Bias check flags |r| > 0.6; results reported transparently. |
| CPU memory overflow | Streaming load, batch size = 32, fallback to random subset if needed. |