# Research: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

## Research Question
Do lightweight, heterophily‑aware Graph Neural Networks trained on the QM9 dataset outperform a traditional Random Forest baseline (Morgan fingerprints) in predicting the HOMO‑LUMO gap—a proxy for molecular reactivity—under strict CPU‑only constraints?

## Dataset Strategy

| Dataset | Purpose | Source (Verified) | Access Method | Constraints/Notes |
|---|---|---|---|---|
| **QM9 (Parquet)** | Primary training data (SMILES + DFT properties). | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | `torch_geometric.datasets.QM9` (streaming) | Loaded via streaming to stay within RAM. Target property: `homo_lumo_gap = lumo - homo`. |
| **Reference Substructures** | Ground truth for attribution (FR‑008). | Curated from *J. Chem. Inf. Model.* 2020, 60, 12, 5785‑5796 (Table 2). | Static CSV (`data/raw/reference_substructures_raw.csv`). | 50 curated SMILES with DOIs. |
| **Kinetic Dataset** | Proxy validation of HOMO‑LUMO gap (FR‑009). | Curated from *J. Phys. Chem. A* 2018, 122, 15, 4053‑4062 (Table 3). | Static CSV (`data/raw/kinetic_dataset_raw.csv`). | ≥ 20 molecules, experimental rates. |

### Decision/Rationale
- **CPU‑First**: QM9 is streamed; all model code runs with `device='cpu'`. GPU escape hatch is only a fallback for OOM, not part of the primary path.
- **Verified Sources**: All URLs appear in the “Verified datasets” block; no invented sources.
- **Missing Public DFT‑gap Source**: The DFT‑calculated HOMO‑LUMO gap is not directly available; we compute it from the `homo` and `lumo` columns in QM9 (allowed by the spec’s assumption).

## Methodology

### 1. Data Ingestion & Preprocessing (FR‑001)
- **Download**: `torch_geometric.datasets.QM9` streams each molecule to `data/raw/qm9_subset.parquet`.
- **Graph Construction**: RDKit parses SMILES → `torch_geometric.data.Data` with node features (atomic number, hybridization, formal charge) and edge features (bond type, conjugation, in‑ring flag).
- **Invalid SMILES**: Logged to `artifacts/exclusion_report.json`; exclusion rate must stay < 0.1 % (SC‑005).
- **Scaffold Split**: Murcko scaffold split (80 % train, 20 % test). Test molecules with Tanimoto similarity > 0.8 to any training molecule are moved to a “near‑miss” holdout to enforce true generalization.

### 2. Model Training (FR‑002, FR‑003)
- **Spectral GNN**: Chebyshev convolution (3 layers, hidden dim = 64). Early stopping on validation loss; max 50 epochs.
- **Heterophily‑aware GNN**: VR‑GNN‑style (graph‑propagation with residuals). Same training regime.
- **Random Forest Baseline**: Morgan fingerprints (radius 2, nBits = 2048) → `sklearn.ensemble.RandomForestRegressor`.
- **Memory Safety**: Batch size auto‑reduced if RAM > 4 GB; adjustments logged (`artifacts/memory_adjustment.log`).

### 3. Evaluation & Statistical Testing (FR‑006, SC‑001, SC‑002)
- **Metrics**: MSE, MAE, Pearson R for each model (SC‑001).
- **Paired t‑test**: Compare each GNN’s error vector against the RF error vector on the scaffold‑split test set; Bonferroni correction for the three metric comparisons (SC‑002). Significance threshold α = 0.05 (source: 2203.15897, https://arxiv.org/abs/2203.15897).

### 4. Feature Attribution (FR‑005, SC‑003)
- **GNNExplainer**: Run on 100 random test molecules; output per‑molecule node/edge importance and top‑5 substructures.
- **Alignment Score**: For each molecule compute Tanimoto similarity between the explained substructure and every entry in the curated reference set; take the maximum. Average across molecules → **Mean‑max Tanimoto Similarity (MMTS)**.  
- **Success Criterion**: MMTS ≥ 0.7 (SC‑003). A null‑model baseline (random subgraph) is also computed; MMTS must exceed null + 0.1.

### 5. Proxy Validation (FR‑009, SC‑006)
- **Correlation Check**: Plot predicted HOMO‑LUMO gaps vs. experimental reaction rates from the kinetic dataset (filtered to thermodynamically‑controlled reactions). Compute Pearson R for trend illustration only; no formal hypothesis test due to n = 20.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Bonferroni applied (α_adj = 0.05/3 ≈ 0.0167).  
- **Power**: Sample size fixed by QM9; we assume sufficient power for medium‑large effect sizes; limitation noted.  
- **Causal Claims**: None; all statements are associational.  
- **Collinearity**: Node/edge features are inter‑related; importance is reported descriptively, not as independent causal effects.  
- **Independence**: Post‑hoc error‑correlation check (T032) will switch to Wilcoxon signed‑rank if errors are not independent.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| QM9 download failure | Exponential backoff (max 3 attempts) with clear error code. |
| Memory OOM during graph construction | Streamed processing; dynamic batch‑size reduction; fallback to 10 k‑molecule sample if needed. |
| Invalid SMILES exceed 0.1 % | Log and abort; investigate source dataset integrity. |
| HOMO‑LUMO gap weak proxy for reactivity | Validate trend against kinetic dataset; explicitly report limitation. |

---
