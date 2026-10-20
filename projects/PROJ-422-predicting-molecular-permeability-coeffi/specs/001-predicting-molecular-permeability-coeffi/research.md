# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We evaluate whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting **experimental permeability coefficients**. The target must be an independent experimental measurement; no surrogate (e.g., logP) will be used.

## 2. Dataset Strategy

### 2.1 Verified Open Datasets
Only the following open datasets (verified URLs) are available for download via the Hugging Face `datasets` library:

| Dataset | URL | Format | Variables |
|---------|-----|--------|-----------|
| **ChEMBL‑derived RDKit descriptors** | `https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Parquet | `smiles`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds` |
| **Half‑ChEMBL RDKit descriptors** | `https://huggingface.co/datasets/fabikru/half-of-chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Parquet | Same as above |
| **SMILES‑Transformers** | `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet` | Parquet | `smiles` only |
| **SELFormer SMILES** | `https://huggingface.co/datasets/HUBioDataLab/SELFormer-smiles/resolve/main/data.csv` | CSV | `smiles` only |
| **TPSA / GRAPO** | `https://huggingface.co/datasets/Alan123/hba_hbd_tpsa_grpo/resolve/main/data/train-00000-of-00001.parquet` | Parquet | `smiles`, `tpsa`, `hba`, `hbd` |
| **RDKit (generic)** | `https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet` | Parquet | `smiles` + a set of RDKit descriptors |

**No verified source contains experimental permeability measurements.** Consequently, FR‑001 (acquire a permeability dataset) cannot be satisfied with the current open data. The research plan therefore **flags this as a specification limitation** and will stop after preprocessing, emitting a clear warning. A future revision of the specification should either (a) provide an open permeability benchmark or (b) formally permit the use of a surrogate target after appropriate justification.

### 2.2 Target Selection (Current Limitation)
- **If** a dataset with a true `permeability` column is later added, it will be used as the regression target.
- **Otherwise**, the pipeline halts after preprocessing; no model training or evaluation occurs, preserving statistical rigor (Constitution VII).

### 2.3 Data Volume & Streaming
All listed datasets are ≤ 1 GB each. We will load them with `datasets.load_dataset(..., streaming=True)` to keep RAM usage low while processing the full dataset.

## 3. Methodology

### 3.1 Feature Engineering
1. **SMILES → Graph** using `rdkit.Chem.MolFromSmiles`. Invalid SMILES are logged and excluded (FR‑011).  
2. **Node Features**: atomic number, degree, formal charge, hybridization, aromatic flag.  
3. **Edge Features**: bond type, conjugation flag.  
4. **Standard Descriptors** (RDKit): MW, TPSA, H‑bond acceptors/donors, rotatable bonds, logP (included for completeness but never used as target).  
5. **Graph‑Derived Statistics** (for RF‑ablation): mean node degree, graph density, aromatic‑ring count, counts of functional groups (carbonyl, amine, etc.).  

All transformations output a Parquet file `data/processed/processed_data.parquet` that conforms to `contracts/dataset.schema.yaml`.

### 3.2 Model Architectures
- **MPNN (GNN)**: 3 message‑passing layers, hidden dimension = 64, global mean pooling, linear regression head. Trained with Adam (`lr=0.001`), batch size = 32, early stopping (patience = 5) on validation loss. CPU‑only (`device="cpu"`).  
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`. Trained on the full descriptor vector.  
- **Random Forest Ablation**: Same hyper‑parameters, trained **only** on graph‑derived statistics (no standard descriptors) to isolate topological value (FR‑013).

### 3.3 Training & Evaluation (only when `target` is present)
- **Split**: Train / test split (ratio deferred) stratified by `polymer_type` when available; otherwise random with fixed seed `42`.  
- **A‑priori Power Analysis**: Using `statsmodels.stats.power.tt_ind_solve_power` to compute required N for a medium effect (Cohen’s d = 0.5) at α = 0.05, 80 % power. The planned sample size and achieved power are recorded; if the actual N is smaller, a “limited power” flag is logged (SC‑004).  
- **Metrics**: RMSE, MAE, R² on the held‑out test set.  
- **Statistical Test**:  
  1. Shapiro‑Wilk test on paired error differences.  
  2. If normal (p ≥ 0.05) → paired two‑sample t‑test; else → Wilcoxon signed‑rank test.  
  3. Record method, p‑value, and significance decision (SC‑001, SC‑002).  
- **Effect Size**: Compute Cohen’s d for the paired differences; store in results.  

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the descriptor baseline (and on the ablation model); mean absolute SHAP values are ranked and plotted.  
- **GNNExplainer**: Run on 100 random test molecules; aggregate subgraph masks to a global importance ranking of functional groups/substructures; visualized as heatmaps.  
- Outputs are saved under `results/interpretability/`.

### 3.5 Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No true permeability data | Flag spec limitation; halt before training to avoid circular validation. |
| Small dataset → overfitting | Early stopping, modest hidden size, dropout = 0.1, RF ablation baseline. |
| Invalid SMILES | RDKit parsing guard; log & drop; retention check ensures ≥ 95 % valid molecules (FR‑011). |
| High correlation between descriptors & target (proxy risk) | Bias check (FR‑014) flags |r| > 0.6; reported transparently. |
| CPU memory overflow | Streaming load, batch size = 32, fallback to random subset if needed. |

---
