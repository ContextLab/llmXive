# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We evaluate whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting **experimental permeability coefficients** of polymeric membranes. The target must be an independent experimental measurement; no surrogate (e.g., logP) will be used **unless** the specification is amended to permit a justified surrogate (see Phase 0 of the plan).

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

**No verified source contains experimental permeability measurements.** Consequently, FR‑001 (acquire a permeability dataset) cannot be satisfied with the current open data. The pipeline therefore **halts after preprocessing** if no `permeability` column is detected, emitting a clear limitation warning (Constitution VII).  

**Spec‑amendment path:** If the project stakeholders approve using a chemically justified surrogate target (e.g., `logP`, which is known to correlate with membrane permeability), the plan will treat that column as the regression target and proceed with modeling. This amendment must be recorded in the project state file.

### 2.2 Target Selection (Current Limitation)
- **If** a dataset with a true `permeability` column is later added, it will be used as the regression target.
- **If** a surrogate target is approved, the chosen column (e.g., `logP`) will be used and the analysis will note the surrogate nature throughout.
- **Otherwise**, the pipeline stops after preprocessing; no model training or evaluation occurs, preserving statistical rigor.

### 2.3 Data Volume & Streaming
All listed datasets are ≤ 1 GB each. We will load them with `datasets.load_dataset(..., streaming=True)` to keep RAM usage low while processing the full dataset.

## 3. Methodology

### 3.1 Feature Engineering
1. **SMILES → Graph** using `rdkit.Chem.MolFromSmiles`. Invalid SMILES are logged and excluded (FR‑011).  
2. **Node Features**: atomic number, degree, formal charge, hybridization, aromatic flag.  
3. **Edge Features**: bond type, conjugation flag.  
4. **Standard Descriptors** (RDKit): MW, TPSA, H‑bond acceptors/donors, rotatable bonds, logP.  
5. **Graph‑Derived Statistics** (for RF‑ablation): mean node degree, graph density, aromatic‑ring count, functional‑group counts (carbonyl, amine, etc.).  

All transformations output a Parquet file `data/processed/processed_data.parquet` **and** a CSV `processed_data.csv` that conform to `contracts/dataset.schema.yaml`.

### 3.2 Model Architectures
- **MPNN (GNN)**: 3 message‑passing layers, hidden = 64, global mean pooling, linear regression head. Trained with Adam (`lr=0.001`), batch size = 32, early stopping (patience = 5) on validation loss. CPU‑only (`device="cpu"`).  
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`. Trained on the full descriptor vector.  
- **Random Forest Ablation**: Same hyper‑parameters, trained **only** on graph‑derived statistics (no standard descriptors) to isolate topological value (FR‑013).

### 3.3 Training & Evaluation (only when `target` is present or surrogate approved)
- **Split**: Train / test split (ratio deferred) stratified by `polymer_type` when available; otherwise random with fixed seed `42`.  
- **A‑priori Power Analysis**: Using `statsmodels.stats.power.tt_ind_solve_power` to compute required N for a medium effect (Cohen’s d = 0.5) at α = 0.05, 80 % power. Record planned size; if actual N is smaller, log a “limited power” flag (SC‑004).  
- **Metrics**: RMSE, MAE, R² on the held‑out test set.  
- **Statistical Test**:  
  1. Shapiro‑Wilk test on paired error differences.  
  2. If normal (p ≥ 0.05) → paired two‑sample t‑test; else → Wilcoxon signed‑rank test.  
  3. Record method, p‑value, and significance decision (SC‑001, SC‑002).  
- **Effect Size**: Compute Cohen’s d for the paired differences; store in results.  

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the descriptor baseline (and on the ablation model); mean absolute SHAP values are ranked and plotted.  
- **GNNExplainer**: Run on a representative set of random test molecules; aggregate subgraph masks to a global importance ranking of functional groups/substructures; visualized as heatmaps.  
- **Cross‑Model Comparison**: Instead of a cross‑feature Spearman correlation, we compute an **overlap‑count metric**: each top‑5 GNN‑identified substructure is mapped to the most chemically related standard descriptor (e.g., aromatic ring → logP, H‑bond donor groups → HBD). We then count how many of the top‑5 mapped descriptors overlap with the top‑5 SHAP‑ranked descriptors. The metric reports the integer overlap (0–5) and a boolean flag `overlap_meets_threshold` (true if overlap ≥ 3), satisfying SC‑003.  

All outputs are saved under `results/interpretability/`.

### 3.5 Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No true permeability data | Flag spec limitation; halt before training to avoid circular validation. |
| Small dataset → overfitting | Early stopping, modest hidden size, dropout = 0.1, RF ablation baseline. |
| Invalid SMILES | RDKit parsing guard; log & drop; retention check ensures ≥ 95 % valid molecules (FR‑011). |
| High correlation between descriptors & target (proxy risk) | Bias check (FR‑014) flags |r| > 0.6; reported transparently. |
| CPU memory overflow | Streaming load, batch size = 32, fallback to random subset if needed. |

---

