# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We evaluate whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting **experimental permeability coefficients**. **Crucially, the target must be an independent measurement**, not a derived descriptor.

## 2. Dataset Strategy

### 2.1 Verified Datasets
Only the following open datasets (verified URLs) are available:

| Dataset | URL | Format | Variables of interest |
|---------|-----|--------|-----------------------|
| **ChEMBL‑derived RDKit descriptors** | `https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Parquet | `smiles`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds` |
| **Half‑ChEMBL RDKit descriptors** | `https://huggingface.co/datasets/fabikru/half-of-chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Parquet | Same as above |
| **SMILES‑Transformers** | `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet` | Parquet | `smiles` only |
| **SELFormer SMILES** | `https://huggingface.co/datasets/HUBioDataLab/SELFormer-smiles/resolve/main/data.csv` | CSV | `smiles` only |
| **TPSA / GRAPO** | `https://huggingface.co/datasets/Alan123/hba_hbd_tpsa_grpo/resolve/main/data/train-00000-of-00001.parquet` | Parquet | `smiles`, `tpsa`, `hba`, `hbd` |

**No verified source contains experimental permeability measurements.** Consequently, FR‑001 (ingestion of permeability datasets) cannot be satisfied with the current open data. The research plan therefore **flags this as a specification limitation** and recommends a scope revision to either (a) locate an open permeability dataset (e.g., a newly released benchmark) or (b) formally amend the specification to allow a surrogate target **only after the specification is updated**. Until such a dataset is identified, the pipeline will stop after preprocessing and will **not** proceed to model training.

### 2.2 Target Selection (Current Limitation)
- **If** a dataset with a true `permeability` column is found, it will be used as the target.
- **Otherwise**, the pipeline stops after preprocessing with an informative warning, avoiding circular use of any descriptor (e.g., `logP`) as a target.

### 2.3 Data Volume & Streaming
Each Parquet file is ≤ 1 GB; we enable streaming (`datasets.load_dataset(..., streaming=True)`) to keep memory usage low while processing the full dataset.

## 3. Methodology

### 3.1 Feature Engineering
1. **SMILES → Graph** using `rdkit.Chem.MolFromSmiles`. Invalid SMILES are logged and excluded (FR‑010).  
2. **Node Features**: atomic number, degree, formal charge, hybridization, aromatic flag.  
3. **Edge Features**: bond type, conjugation flag.  
4. **Standard Descriptors** (RDKit): MW, TPSA, H‑bond acceptors/donors, rotatable bonds (logP is **excluded** unless it is the target, which it will not be in the current pipeline).  
5. **Graph‑Derived Statistics** (for RF‑ablation): mean node degree, graph density, aromatic‑ring count, functional‑group counts (e.g., carbonyl, amine).  

All transformations produce `data/processed/processed_data.parquet` conforming to `contracts/dataset.schema.yaml`.

### 3.2 Model Architectures
- **MPNN (GNN)**: 3 message‑passing layers, hidden = 64, global mean pooling, linear regression head. Trained with Adam (`lr=0.001`), batch size = 32, early stopping (patience = 5) on validation loss. CPU‑only (`device="cpu"`).  
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`. Trained on the full descriptor vector.  
- **Random Forest Ablation**: Same hyper‑parameters, trained **only** on graph‑derived statistics (no standard descriptors).

### 3.3 Training & Evaluation
- **Split**: [deferred] train / [deferred] test, stratified by `polymer_type` when present; otherwise random with fixed seed.
- **A‑priori Power Analysis**: Before training, compute required sample size for a medium effect (Cohen’s d = 0.5) at α = 0.05, 80 % power using `statsmodels`. Record planned size and achieved power; if the dataset is smaller, flag limited power in the results (methodology‑68ef9d7e).  
- **Metrics**: RMSE, MAE, R² on the held‑out test set.  
- **Statistical Test**:  
  1. Perform Shapiro‑Wilk normality test on the paired error differences.  
  2. If normal (p ≥ 0.05) → paired two‑sample t‑test; else → Wilcoxon signed‑rank test.  
  3. Record method, p‑value, and significance decision (SC‑002, methodology‑743d42e3).  
- **Effect Size & Power**: Compute Cohen’s d and post‑hoc power; store in results.  

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the descriptor baseline (and on the ablation model); mean absolute SHAP values are ranked and plotted.  
- **GNNExplainer**: Run on 100 random test molecules; aggregate subgraph masks to a global importance ranking of functional groups/substructures; visualized as heatmaps.  
- Outputs are saved under `results/interpretability/`.

### 3.5 Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No true permeability data | Flag spec limitation; halt before training to avoid circular validation. |
| Small dataset → overfitting | Early stopping, modest hidden size, dropout (0.1), ablation study. |
| Invalid SMILES | RDKit parsing guard; log & drop; retention check ensures ≥ 95 % valid molecules (FR‑011). |
| High correlation between descriptors & proxy target | Bias check (FR‑013) flags \|r\| > 0.85; reported transparently. |
| CPU memory overflow | Streaming load, batch size = 32, fallback to random subset if needed. |

---

