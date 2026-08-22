# Research: Predicting Molecular Interactions in Protein-Ligand Complexes Using Graph Neural Networks

## Executive Summary

This research validates the feasibility of predicting protein-ligand binding affinity (pKd) using a Graph Neural Network (GNN) trained on the PDBbind v2020 refined set. The approach encodes 3D steric constraints as distance-based edges in a heterogeneous graph, trains a 3-layer message-passing network, and applies Integrated Gradients to identify recurring molecular motifs. The study confirms that the dataset contains the necessary variables (3D coordinates, pKd) and that the method is computationally feasible on CPU-first infrastructure with a GPU escape hatch for scaling. **Claims are explicitly framed as associational.** No causal inference is made; the study identifies correlations between substructure motifs and binding affinity, validated by statistical enrichment tests.

## Dataset Strategy

### Verified Datasets

The project relies exclusively on the following verified, open-source datasets:

| Dataset Name | Source URL | Format | Variables | Access Method |
|--------------|------------|--------|-----------|---------------|
| PDBbind v2020 Refined | https://huggingface.co/datasets/jglaser/pdbbind_complexes/resolve/main/data/pdbbind.parquet | Parquet | 3D coordinates (x, y, z), atom types, pKd, resolution | `datasets.load_dataset(..., streaming=True)` |
| PDBbind Full (Reference) | https://huggingface.co/datasets/HUBioDataLab/pdbbind_full/resolve/main/pdbbind_full.csv | CSV | Full set metadata | `datasets.load_dataset(...)` |
| PDBbind Processed | https://huggingface.co/datasets/DaInternet12/pdbbind_affinities/resolve/main/pdbbind_processed.parquet | Parquet | Affinity metadata only | `datasets.load_dataset(...)` |
| Gold Standard Subset (Raw PDB) | ftp://ftp.wwpdb.org/pub/pdb/data/structures/divided/pdb/ | PDB | Raw crystallographic coordinates including waters | FTP download (manual subset) |

**Primary Source**: `jglaser/pdbbind_complexes` (Parquet) is selected as the primary source for its structured format and verified availability. It contains the necessary 3D coordinates and pKd values required by FR-001 and FR-002.

**Data Availability & Feasibility**:
- **Downloadability**: The dataset is hosted on Hugging Face and accessible via the `datasets` library without authentication or credentials, satisfying the CI runner's unattended execution requirement.
- **Variable Fit**: The dataset contains 3D atomic coordinates (essential for steric edge construction) and experimental pKd values (target variable). No critical variables are missing.
- **Water Limitations**: The "refined" set in PDBbind (and most processed subsets like the Hugging Face parquet source) **explicitly excludes water molecules** by definition to focus on the protein-ligand interaction core. The plan's reliance on a heuristic to flag water-mediated interactions (FR-009) is validated against a separate, small "Gold Standard" subset of raw PDB files (downloaded via FTP) that *do* contain explicit waters. This validates the heuristic's construct validity without requiring the main dataset to contain the missing data.
- **Memory Management**: The full dataset ([deferred] complexes) will be processed via streaming (`streaming=True`) to avoid loading all graphs into RAM simultaneously. Graphs are constructed on-the-fly and saved to disk in `data/processed/`.

## Methodological Rigor

### Graph Construction (FR-001)

- **Node Features**: Atom type, formal charge, hydrophobicity (derived via RDKit).
- **Edge Construction**: 
  - Covalent bonds: Detected via RDKit bond orders.
  - Non-covalent edges: Created for atom pairs within a 5.0 Å cutoff (steric constraint).
  - **3D Sensitivity**: A sensitivity analysis (Phase 1.3) will vary the cutoff (4.0, 5.0, 6.0 Å) to quantify edge count variance and model performance variance, addressing the "hard threshold" concern.
- **Missing Hydrogens**: Hydrogens are inferred using RDKit's `AddHs` based on standard valency. Complexes with unresolved valency are flagged for exclusion.
- **Ablation Study**: An ablation study (T023b) will train the model without explicit distance features to distinguish between learning geometry and memorizing coordinates, addressing the "definitional redundancy" concern.

### GNN Training (FR-002)

- **Architecture**: 3-layer Message Passing Neural Network (MPNN) with exactly 128 hidden units.
- **Loss Function**: Mean Squared Error (MSE) on pKd.
- **Optimization**: Adam optimizer with early stopping (patience=10 epochs) to prevent overfitting.
- **Hardware**: CPU-first (PyTorch CPU). If training fails to converge within 4 hours or exceeds RAM, the pipeline triggers the Kaggle GPU escape hatch (scaled-down batch size, 8-bit quantization if necessary).
- **Convergence Criteria**: Spearman correlation > 0.6 on validation set OR max 50 epochs. MSE < 2.0 is reported but not the primary success metric due to its logarithmic scale implications.

### Interpretability & Validation (FR-003 - FR-006)

- **Attribution**: Integrated Gradients applied to the trained model to generate atom-level feature importance scores.
- **Clustering**: DBSCAN (min_cluster_size=5) on high-importance substructures to identify recurring motifs.
- **Statistical Validation**:
  - **Two-Sample T-Test (T035a)**: Compares importance scores of atoms in clusters from high-affinity (pKd > 8) vs. low-affinity (pKd < 6) complexes, as mandated by Constitution Principle VII.
  - **Permutation Test (T035b)**: 1,000 iterations shuffling **motif labels across complexes** (not coordinates) to generate a null distribution for motif enrichment. This preserves 3D structure while testing if the specific motif-affinity association is stronger than random assignment.
  - **Mixed-Effects Model (T035c/T036b)**: Stratifies the null distribution by scaffold identity to control for the confounding effect of common structural scaffolds.
  - **FDR Correction**: Benjamini-Hochberg procedure (alpha=0.05) applied to p-values from motif enrichment tests (FR-006).
  - **Pharmacophore Matching**: Clusters queried against a reference pharmacophore set (ChEMBL) using the Kabsch algorithm (RMSD < 1.5 Å).
  - **MM-GBSA Fallback (T038b)**: For novel scaffolds where no pharmacophore match is found, MM-GBSA is calculated as a secondary validation, acknowledging its approximate nature and lack of independence from experimental pKd.
- **Causal Claims**: Claims are framed as **associational**. No causal inference is made without randomization; the study identifies correlations between substructure motifs and binding affinity.

### Statistical Rigor Checklist

- **Multiple Comparisons**: Benjamini-Hochberg FDR correction (alpha=0.05) applied to all motif enrichment tests.
- **Sample Size/Power**: The PDBbind v2020 refined set provides sufficient power for an 80/10/10 split. Power limitations are acknowledged if the effective sample size drops due to filtering (e.g., resolution > 2.5 Å).
- **Collinearity**: Edge features (distance) are **definitionally derived** from node coordinates (Euclidean distance). The ablation study (T023b) is included to test if the model learns geometry beyond coordinate memorization.
- **Measurement Validity**: pKd values are experimental measurements from the PDBbind set. Pharmacophore definitions are sourced from established databases (ChEMBL). Water-flagging heuristic is validated against a Gold Standard subset.

## Compute Feasibility

- **CPU-First**: The GNN architecture (a multi-layer configuration) is designed to fit within ~7 GB RAM on a CPU. Graph construction and inference are lightweight enough for the GitHub Actions free tier.
- **GPU Escape Hatch**: If the training loop exceeds a reasonable duration or memory limits, the pipeline automatically re-runs on a Kaggle GPU (16 GB VRAM) with a scaled-down batch size or 8-bit quantization. This ensures real computation without fabrication.
- **Streaming**: Data is streamed to avoid loading the full dataset into memory, ensuring the pipeline runs within the 14 GB disk and 7 GB RAM limits.

## Decision/Rationale

- **Why PDBbind?** It is the only verified, open-source dataset containing 3D coordinates and pKd values for protein-ligand complexes, directly addressing the study's variables.
- **Why GNN?** GNNs are the state-of-the-art for 3D molecular property prediction, capable of learning steric constraints via distance-based edges.
- **Why CPU-First?** To ensure reproducibility on free-tier CI runners. The GPU escape hatch is a fallback, not the primary design, to prevent fabrication of results on inaccessible hardware.
- **Why Benjamini-Hochberg?** Standard practice for controlling Type I errors in multiple hypothesis testing (motif enrichment), as mandated by FR-006 and Principle VII.
- **Why T-Test?** Required by Constitution Principle VII for motif validation.
- **Why Mixed-Effects Model?** To control for scaffold frequency confounding in motif enrichment analysis.
