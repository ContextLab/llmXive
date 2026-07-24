# Research: Predicting Molecular Permeability Coefficients via Graph Neural Networks

## Executive Summary

This research investigates whether Graph Neural Networks (GNNs) can outperform traditional descriptor-based models (Random Forest, Linear Regression) in predicting general molecular permeability coefficients (ADMET) using graph representations (atoms as nodes, bonds as edges). The study utilizes the ChEMBL ADMET dataset, as no verified open-source dataset for polymeric membranes exists. The analysis is strictly associational, acknowledging the observational nature of the data and the domain shift from polymeric membranes to ADMET.

## Dataset Strategy

The project relies on the "Verified datasets" block provided in the specification. We must confirm that the selected datasets contain **both** SMILES strings and experimental permeability coefficients for general molecular permeability (ADMET).

### Verified Datasets & Selection

| Dataset Name | Source URL | Relevance to Permeability | Status |
|:--- |:--- |:--- |:--- |
| **ChEMBL (with RDKit Descriptors)** | ` | Contains SMILES and pre-computed descriptors. **Critical Check**: Does it contain permeability coefficients (e.g., P_app, logP) for *general ADMET*? **Yes**, this is the primary source. | **Primary** |
| **PubChem (10M)** | ` | Massive SMILES repository. **Critical Check**: Likely lacks specific permeability coefficients; may be used for pre-training or descriptor generation only. | **Fallback** (Likely lacks target) |
| **NIST (Parquet)** | ` | **Mismatch**: This dataset appears to be cybersecurity embeddings, not chemical permeability. **DO NOT USE** for molecular data. | **REJECTED** |
| **MTR (Talk to Paul)** | ` | **Mismatch**: Conversational data. **DO NOT USE**. | **REJECTED** |

**Dataset Strategy Rationale**:
1. **Primary Target**: The ChEMBL ADMET dataset is the only verified source containing SMILES and permeability targets.
2. **Domain Shift**: The original research question focused on "polymeric membrane permeability," but no such dataset exists in verified sources. The study is reframed to "General Molecular Permeability (ADMET)" with a clear disclaimer.
3. **Contingency**:
 * **If ChEMBL lacks permeability**: The study will be paused to request a new dataset source. **No fabrication of a "polymeric" dataset will occur.**
 * **Decision**: The plan will proceed by loading the ChEMBL ADMET dataset. If the target column is missing, the study will halt.

*Note: The "Verified datasets" block lists several NIST/PubChem URLs that are clearly non-chemical (cybersecurity, LLM leaderboards). These are identified as mismatches and excluded from the chemical analysis plan.*

## Methodology & Statistical Rigor

### 1. Graph Construction (FR-001)
- **Tool**: `RDKit` (v2023.9.5+).
- **Input**: SMILES strings.
- **Process**:
 1. Parse SMILES to `Mol` object.
 2. Remove salts/inorganics.
 3. Compute baseline descriptors: MW, logP (XLogP3), PSA, Rotatable Bonds.
 4. Convert to Graph: Nodes = Atoms (features: atomic number, hybridization, degree, formal charge), Edges = Bonds (features: bond type, conjugation).
- **Handling Missing Data**: Rows with missing target permeability are excluded (FR-001). Duplicate SMILES with conflicting targets are averaged or flagged.
- **Timeout**: Enforced a fixed timeout for graph construction.

### 2. Model Architecture (FR-002)
- **GNN**: 3-layer Graph Convolutional Network (GCN).
 - **Parameters**: ≤ 500,000.
 - **Layers**: Input -> GCN(64) -> ReLU -> GCN(64) -> ReLU -> GCN(64) -> Global Mean Pooling -> FC(32) -> ReLU -> FC(1).
 - **Regularization**: Dropout (0.5), Weight Decay (1e-4), Early Stopping (patience=10).
 - **Device**: CPU (PyTorch CPU backend).
- **Baselines**:
 - **Random Forest**: 100 trees, max_depth=10.
 - **Linear Regression**: Standard OLS.
- **Input**: GNN uses graph topology; Baselines use descriptor vectors only.

### 3. Cross-Validation & Splitting (FR-003)
- **Split Strategy**: **Scaffold Splitting** (Murcko Scaffolds) to prevent data leakage from similar molecules.
- **Folds**: 5-fold.
- **Metrics**: R², MAE, RMSE.
- **Statistical Test**: **Wilcoxon signed-rank test** (alpha=0.05) comparing GNN vs. RF/LR R² scores across the 5 folds. (Replaces t-test due to small sample size and non-normal distribution assumptions).

### 4. Sensitivity & Uncertainty (FR-004, FR-005)
- **Sensitivity Sweep**: Prediction interval widths {0.01, 0.05, 0.1}. Measure MAE variation.
- **Permutation Importance**: Randomly shuffle specific atom/bond features (substructures) and measure drop in R².
- **Perturbation Experiment**: For SC-004, specific functional groups (hydroxyl, carboxyl, amine) are removed from molecules, and the change in predicted permeability is checked against chemical intuition.
- **Causal Disclaimer**: All conclusions framed as "associational" (FR-006).

### 5. Compute Feasibility (FR-007)
- **CPU-First**: The small parameter count (≤500K) and [deferred] dataset size are designed to run on 2 cores / 7GB RAM within 2 hours.
- **GPU Escape Hatch**: If the training step exceeds 2 hours on CPU, the execution agent will automatically re-run on a Kaggle GPU (scaled down: 8-bit quantization or fewer epochs) as per the "Compute feasibility" rules.
 - **Reproducibility**: The Kaggle run uses a pinned Docker image (`pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime`) and a specific Kaggle kernel ID to ensure the environment is identical to the local CPU run.
 - **No Synthetic Approximation**: No synthetic CPU approximation of a GPU-only method is planned.

## Data Availability & Risks

- **Risk**: The "Verified datasets" block lacks a confirmed source for *polymeric membrane* permeability.
- **Mitigation**: The study has been reframed to "General Molecular Permeability (ADMET)". The ChEMBL ADMET dataset is used as a proxy. A prominent disclaimer will be included in the final report stating the domain shift.
- **Streaming**: If the dataset exceeds memory, `datasets.load_dataset(..., streaming=True)` will be used to process shards sequentially.

## References

- **ChEMBL ADMET Dataset**: ` (Verified Source).
- **RDKit**: ` (Standard Library).
- **PyTorch Geometric**: ` (Standard Library).

*Note: URLs for NIST, PubChem, and MTR listed in the "Verified datasets" block were inspected and found to be non-chemical (cybersecurity, LLM, conversational) or mismatched. They are excluded from the chemical analysis plan.*