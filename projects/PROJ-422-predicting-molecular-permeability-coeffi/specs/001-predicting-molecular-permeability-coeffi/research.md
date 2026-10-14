# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We aim to assess whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting molecular permeability‑related properties. Because no open dataset supplies experimental permeability coefficients, the study pivots to a **Feasibility Study** that predicts the calculated `logP` descriptor (derived from SMILES) as a proxy target. The central hypothesis remains: **graph topology captures predictive information beyond standard descriptors**, even when the target itself is a descriptor.

## 2. Dataset Strategy

### 2.1 Verified Datasets
Only the following open datasets (verified URLs) will be used:

| Dataset | URL | Format | Variables of interest |
|---------|-----|--------|-----------------------|
| **ChEMBL‑derived RDKit descriptors** | `https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Parquet | `smiles`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds` |
| **Half‑ChEMBL RDKit descriptors** | `https://huggingface.co/datasets/fabikru/half-of-chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Parquet | Same as above |
| **SMILES‑Transformers** | `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet` | Parquet | `smiles` only (used for supplemental size) |
| **SELFormer SMILES** | `https://huggingface.co/datasets/HUBioDataLab/SELFormer-smiles/resolve/main/data.csv` | CSV | `smiles` only |
| **TPSA / GRAPO** | `https://huggingface.co/datasets/Alan123/hba_hbd_tpsa_grpo/resolve/main/data/train-00000-of-00001.parquet` | Parquet | `smiles`, `tpsa`, `hba`, `hbd` |

*No verified source contains experimental permeability coefficients; therefore the proxy target `logP` is adopted (see Section 2.2).*

### 2.2 Proxy Mode & Target Selection
- If a dataset includes a column named `logp` (calculated by RDKit), it will be used as the **target**.
- If `logp` is absent, we will compute it on‑the‑fly via RDKit and store it as `target`.
- All other columns are treated as **input descriptors** for the RF baseline; the graph representation is derived from the SMILES.

### 2.3 Data Volume & Streaming
- Each Parquet file is ≤ 1 GB; streaming is enabled (`datasets.load_dataset(..., streaming=True)`) to guarantee low memory usage and to allow processing of the full dataset without RAM overflow.

## 3. Methodology

### 3.1 Feature Engineering
1. **SMILES → Graph** using `rdkit.Chem.MolFromSmiles`. Invalid SMILES are logged and excluded (FR‑010).  
2. **Node Features**: atomic number, degree, formal charge, hybridization, aromatic flag.  
3. **Edge Features**: bond type, conjugation flag.  
4. **Standard Descriptors**: MW, logP, TPSA, HBA, HBD, Rotatable Bonds (RDKit `Descriptors`).  
5. **Graph‑Derived Statistics** (for RF ablation): mean node degree, graph density, counts of aromatic rings, counts of common functional groups (e.g., carbonyl, amine).  

All transformations produce a new file under `data/processed/processed_data.parquet` that conforms to `contracts/dataset.schema.yaml`.

### 3.2 Model Architectures
- **MPNN (GNN)**: 3 message‑passing layers, hidden dimension = 64, ReLU activation, global mean pooling, final linear head → scalar regression. Trained with Adam (`lr=0.001`), batch size = 32, early stopping (patience = 5) on validation loss. CPU‑only (`device="cpu"`).  
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`, trained on the full descriptor vector.  
- **Random Forest Ablation**: Same RF hyper‑parameters, trained on the graph‑derived statistics only (no standard descriptors).  

### 3.3 Training & Evaluation
- **Split**: 80 % train / 20 % test, stratified by `polymer_type` if present; otherwise random with a fixed seed.  
- **Metrics**: RMSE, MAE, R² (computed on the held‑out test set).  
- **Statistical Test**: Paired two‑sample t‑test on per‑sample absolute errors (GNN vs. RF baseline). Significance threshold `p < 0.05` (SC‑002).  
- **Effect Size & Power**: Compute Cohen’s d, 95 % confidence interval for the mean error difference, and a post‑hoc power estimate using the observed effect size and `n_test`. All values stored in `results/metrics.json`.  

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the descriptor baseline; mean absolute SHAP values are ranked.  
- **GNNExplainer**: Run on a random subset of 100 test molecules; subgraph masks are aggregated to produce a global importance ranking of functional groups/substructures.  
- Visualizations: bar charts for SHAP, heatmaps for GNNExplainer masks, both saved under `results/interpretability/`.

### 3.5 Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No permeability target | Proxy `logP` target; explicit disclaimer in final report. |
| Small dataset → overfitting | Early stopping, dropout (0.1), small hidden size, ablation study. |
| Invalid SMILES | RDKit parsing guard, log & exclude; retention check ensures ≥ 95 % valid molecules (FR‑011). |
| High correlation between descriptors & proxy target | Bias check (FR‑013) flags |r| > 0.85; report as expected for proxy. |
| CPU memory overflow | Streaming load, batch processing, max‑batch‑size = 32, fallback to smaller subset if needed. |

---
