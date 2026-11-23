---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Ionization Energies with Graph Neural Networks

**Field**: chemistry

## Research question

To what extent can 2D graph-based representations of small organic molecules approximate ionization energies derived from high-level quantum calculations, and which specific local structural features (e.g., functional groups, bond orders) drive this predictive signal independent of 3D geometric conformation?

## Motivation

High-level quantum chemical calculations (e.g., CCSD(T)) for ionization energies are accurate but computationally prohibitive for large-scale molecular screening. While Graph Neural Networks (GNNs) offer a faster alternative, it remains unclear whether 2D topology alone captures sufficient electronic information to approximate ionization potentials or if 3D conformational data is strictly required. This project addresses the gap in understanding the sufficiency of 2D structural descriptors for electronic property prediction, enabling efficient pre-screening of chemical libraries without expensive geometry optimization.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using terms focused on "graph neural networks for ionization potential prediction," "deep learning models for molecular ionization energy," and "machine learning prediction of vertical ionization energies." The search yielded a sparse set of results directly addressing the specific intersection of 2D GNNs and ionization energy prediction, with most literature focusing on general molecular regression benchmarks or 3D-dependent quantum machine learning methods.

### What is known

- [Benchmarking ionization potentials from the simple pCCD model (2023)](https://arxiv.org/abs/2304.14810) — Establishes that ionization potential is a fundamental observable in photoelectron spectroscopy and highlights the challenge of accurately modeling electron-detachment energies with simplified quantum models, suggesting a need for data-driven approximations.

### What is NOT known

There is no published work that explicitly quantifies the performance ceiling of *strictly* 2D graph representations (excluding 3D coordinates and conformer ensembles) for predicting ionization energies specifically, nor is there a systematic analysis isolating which 2D structural features (e.g., specific heteroatom environments vs. global topology) contribute most to the predictive signal for this electronic property.

### Why this gap matters

Filling this gap is critical for computational chemistry workflows: if 2D graphs are sufficient, researchers can bypass costly 3D conformer generation and quantum geometry optimization for initial property screening, significantly accelerating drug discovery and materials design. Conversely, identifying the limitations of 2D models clarifies where expensive 3D-aware methods are strictly necessary.

### How this project addresses the gap

This project will train a Message-Passing Neural Network (MPNN) exclusively on 2D molecular graphs derived from the QM9 dataset (using -HOMO as a proxy for ionization energy via Koopmans' theorem) and perform ablation studies to quantify the predictive contribution of specific 2D features. By comparing the 2D GNN's performance against a baseline that requires 3D inputs (if feasible within constraints) or theoretical limits, we will directly measure the information loss incurred by ignoring 3D geometry.

## Expected results

We expect to find that local substructures (e.g., conjugated pi-systems, electronegative heteroatoms) dominate the predictive signal, allowing a 2D-only model to achieve a Mean Absolute Error (MAE) < 0.5 eV relative to the -HOMO proxy. We anticipate that the inclusion of 3D coordinates will yield diminishing returns for rigid molecules but may improve accuracy for flexible systems, quantifiable through the proposed ablation studies.

## Methodology sketch

- **Data Acquisition**: Download the QM9 dataset from the HuggingFace Datasets repository (`qm9`), which provides SMILES strings and DFT-computed molecular orbitals (HOMO/LUMO) for ~134k molecules.
- **Target Variable Construction**: Derive the target variable "Ionization Energy" using Koopmans' theorem approximation ($IE \approx -\epsilon_{HOMO}$), explicitly acknowledging this as a proxy for the ground-truth ionization potential.
- **Feature Engineering**: Convert SMILES strings to 2D molecular graphs using RDKit, extracting atom features (element, hybridization, charge) and bond features (order, conjugation, ring membership) without generating 3D coordinates.
- **Model Architecture**: Implement a Message-Passing Neural Network (MPNN) using PyTorch Geometric, configured for CPU execution with a batch size $\le$ 64 to fit within 7GB RAM constraints.
- **Training Protocol**: Split the dataset using scaffold-based splitting (Bemis-Murcko scaffolds) to ensure the test set contains chemically distinct scaffolds from the training set, preventing data leakage.
- **Feature Importance Ablation**: Conduct ablation studies by **retraining** the model with specific feature sets zeroed out (e.g., removing bond order information or masking atom types) rather than inference-time noise injection, to isolate the predictive contribution of each structural component.
- **Error Analysis**: Calculate the Pearson correlation between absolute prediction errors and molecular properties (molecular weight, number of rotatable bonds) to determine if model failure correlates with molecular flexibility or size.
- **Baseline Comparison**: Compare the 2D GNN performance against a simple linear regression model using Morgan fingerprints to establish a non-neural baseline for 2D information sufficiency.
- **Statistical Validation**: Perform a paired t-test on the absolute errors of the full model versus the ablated models across the test set to determine if feature removal results in a statistically significant degradation of performance (p < 0.05).
- **Resource Constraint Adherence**: Execute the entire pipeline (data loading, training, evaluation, ablation) on a single CPU core, ensuring the total runtime does not exceed 6 hours and memory usage remains under 7GB.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-24T04:51:09Z
**Outcome**: exhausted
**Original term**: Predicting Molecular Ionization Energies with Graph Neural Networks chemistry
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Molecular Ionization Energies with Graph Neural Networks chemistry | 0 |
| 1 | Graph neural networks for ionization potential prediction | 5 |
| 2 | Machine learning models for molecular ionization energy | 0 |
| 3 | Deep learning approaches to vertical ionization energies | 0 |
| 4 | GNN-based property prediction for electronic structure | 0 |
| 5 | Neural network prediction of HOMO energy levels | 0 |
| 6 | Quantum chemical property estimation using graph networks | 0 |
| 7 | Adiabatic ionization energy prediction with deep learning | 0 |
| 8 | Molecular orbital energy prediction via graph convolutional networks | 0 |
| 9 | Data-driven prediction of gas-phase ionization energies | 0 |
| 10 | Graph representation learning for electronic properties | 0 |
| 11 | Hybrid quantum mechanics/machine learning for ionization potentials | 0 |
| 12 | Transfer learning for molecular ionization energy estimation | 0 |
| 13 | Equivariant graph neural networks for electronic structure | 0 |
| 14 | Prediction of first ionization potentials using AI | 0 |
| 15 | Molecular graph embeddings for ionization energy regression | 0 |
| 16 | SchNet and other message-passing networks for ionization energy | 0 |
| 17 | Computational chemistry ionization energy prediction | 0 |
| 18 | Density functional theory benchmarks for GNN ionization models | 0 |
| 19 | Automated discovery of ionization energy trends with GNNs | 0 |
| 20 | Spectral graph theory applications to molecular ionization | 0 |

### Verified citations

1. **Benchmarking ionization potentials from the simple pCCD model** (2023). Saddem Mamache, Marta Gałyńska, Katharina Boguslawski. arXiv. [2304.14810](https://arxiv.org/abs/2304.14810). PDF-sampled: No.
