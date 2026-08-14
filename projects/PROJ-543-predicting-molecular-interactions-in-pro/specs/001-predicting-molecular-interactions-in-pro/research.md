# Research: Predicting Molecular Interactions in Protein-Ligand Complexes Using Graph Neural Networks

## Problem Statement

Can a Graph Neural Network trained on 3D structural data predict protein-ligand binding affinity (pKd) with sufficient accuracy to identify statistically significant, recurring interaction motifs that align with known pharmacophores?

## Dataset Strategy

### Verified Datasets

| Dataset Name | Source URL | Variables Available | Suitability |
|--------------|------------|---------------------|-------------|
| PDBbind v2020 Refined Set | (Official Tarball) | 3D coordinates, atom types, pKd, resolution, water molecules | **Primary**: Contains all required variables (coordinates, affinity, resolution, explicit water) for graph construction and FR-009 water-flagging. |
| BindingDB (Subset) | | Affinity data, structures | **Validation**: Used for external validation on disjoint scaffolds to avoid circularity. |

**Selection Rationale**: The official PDBbind v2020 refined set is selected as the primary source because it is the canonical source for the "refined set" referenced in the spec, ensuring retention of explicit water molecules and accurate resolution metadata required for FR-009 and Constitution Principle VI. Community-converted parquet files are avoided to prevent data fidelity loss.

**Data Availability Check**: The dataset is publicly available via the official PDBbind website. The download script will verify the checksum of the tarball to satisfy Constitution Principle III (Data Hygiene) and Principle I (Reproducibility).

### Dataset Variable Fit

- **Required Variables**: Atom types, 3D coordinates (x, y, z), bond types (implicit via RDKit), pKd, resolution, explicit water molecules.
- **Dataset Fit**: The official PDBbind v2020 refined set contains all these variables.
- **Missing Variables**: None expected. If specific water molecules are missing in the PDB file, FR-009 heuristic (3.5 Å to oxygen) will be applied.
- **Mitigation**: If a complex lacks hydrogens, the pipeline will infer them using RDKit's `AddHs` function (US-1, SC-001).

## Methodology

### 1. Data Ingestion & Graph Construction (US-1)

- **Input**: PDBbind v2020 refined set (official tarball).
- **Process**:
 1. Download and verify checksum.
 2. **Sampling**: Select N=1,000 complexes (random sample) based on power analysis (Cohen's d=0.5, power) to ensure CPU feasibility.
 3. Filter complexes with resolution > 2.5 Å.
 4. Parse 3D coordinates and atom types.
 5. Construct heterogeneous graph:
 - Nodes: Atoms (features: type, charge, hydrophobicity).
 - Edges: Covalent (RDKit) + Non-covalent (distance < 5.0 Å).
 6. **FR-009**: Detect water-mediated interactions using a distance-based heuristic.
 7. **Sensitivity Analysis**: Repeat graph construction with multiple cutoffs.
- **Output**: Serialized graph objects (`.pt` or `.parquet`).

### 2. GNN Training (US-2)

- **Model**: 3-layer Message Passing Neural Network (MPNN) with 128 hidden units.
- **Loss**: Mean Squared Error (MSE) on pKd.
- **Hardware**: CPU-only (GitHub Actions).
- **Constraints**:
 - Max 4 hours training time (FR-007).
 - Early stopping if no improvement for a predefined number of epochs.
 - Batch size tuned to fit available system memory.
- **Split**: 80/10/10 (Train/Val/Test) using **scaffold-based splitting** to ensure chemical diversity.

### 3. Interpretability & Motif Extraction (US-3)

- **Attribution**: Integrated Gradients to compute atom-level importance scores.
- **Alignment**: **Scientific Soundness Fix**: Align high-importance substructures to a common reference frame (Procrustes alignment) before clustering to ensure comparability.
- **Clustering**: DBSCAN (min_samples=5) on aligned substructures.
- **Validation**:
 - **Constitution VII Compliance**: Primary validation via **two-sample t-tests** comparing high-affinity (pKd > 8) and low-affinity (pKd < 6) complexes for each cluster.
 - **Secondary Validation**: Permutation tests (1,000 iterations) with scaffold-aware label shuffling.
 - **FDR Correction**: Benjamini-Hochberg (alpha=0.05).
 - **External Validation**: MM-GBSA on a strictly disjoint scaffold subset (e.g., from BindingDB) to avoid circularity.
- **Ablation**: Validate against random edge removal and feature permutation baselines.

## Statistical Rigor & Feasibility

- **Power Analysis**: N=1,000 selected to detect effect size d=0.5 with 80% power at alpha=0.05.
- **Multiple Comparisons**: Benjamini-Hochberg FDR correction applied to all motif enrichment p-values (FR-006).
- **Causal Claims**: None. All claims are associational (predictive modeling).
- **Collinearity**: Predictors (atom types, distances) are distinct features; no definitional collinearity expected.
- **Structural Dependency**: Permutation test uses scaffold-aware shuffling to account for non-independence of complexes.
- **GPU Escape Hatch**: Not required. The 3-layer GNN is designed to run on CPU with the sampled dataset.

## Decision/Rationale

- **CPU-First**: The GNN architecture (3 layers, 128 units) on N=1,000 samples is lightweight enough for CPU execution.
- **Dataset Choice**: Official PDBbind v2020 is the only source ensuring water molecule retention and resolution metadata fidelity.
- **Statistical Method**: Two-sample t-tests are mandated by Constitution Principle VII; permutation tests are used as a robustness check.
- **Validation Strategy**: External scaffold-based validation ensures motifs are not artifacts of the training distribution.