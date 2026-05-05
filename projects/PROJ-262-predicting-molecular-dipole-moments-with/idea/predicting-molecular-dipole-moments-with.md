# Predicting Molecular Dipole Moments with Graph Neural Networks

**Field**: chemistry

## Research question

Which structural features of small organic molecules (atom types, bond types, 3D conformation) carry the most predictive signal for molecular dipole moments, and how effectively can graph-based representations capture this relationship compared to traditional descriptors?

## Motivation

Molecular dipole moments govern solubility, reactivity, and intermolecular binding, yet their dependence on specific geometric and electronic features is often opaque in black-box models. Understanding which structural components drive dipole predictions is critical for designing interpretable machine learning potentials and guiding synthetic chemistry. This project addresses the gap between high-accuracy property prediction and chemical interpretability.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms: "graph neural network dipole moment prediction", "molecular property prediction feature importance", and "equivariant neural networks chemistry". We examined 4 returned records for relevance to dipole-specific feature decomposition.

### What is known

- [Atomistic Line Graph Neural Network for improved materials property predictions (2021)](https://doi.org/10.1038/s41524-021-00650-1) — Establishes that line-graph GNNs improve general atomistic property prediction over descriptor-based methods.
- [E(3)-equivariant graph neural networks for data-efficient and accurate interatomic potentials (2022)](https://doi.org/10.1038/s41467-022-29939-5) — Demonstrates E(3) equivariance is critical for accurate 3D geometry modeling in potential energy calculations.
- [Graph neural networks for materials science and chemistry (2022)](https://doi.org/10.1038/s43246-022-00315-6) — Reviews the broader application of GNNs in chemistry but does not isolate dipole moments as a primary case study.
- [Learning local equivariant representations for large-scale atomistic dynamics (2023)](https://doi.org/10.1038/s41467-023-36329-y) — Presents efficient parametrizations of potential energy surfaces but does not address electronic property prediction like dipole moments.

### What is NOT known

No published work in the retrieved results explicitly dissects the contribution of atom types versus 3D conformation to dipole moment prediction accuracy. Most cited work focuses on interatomic potentials (energy/forces) rather than electronic properties like dipoles, leaving the specific feature importance landscape for dipoles unquantified.

### Why this gap matters

Without knowing which structural signals drive dipole predictions, chemists cannot trust model recommendations for molecular design or distinguish between physical causality and dataset artifacts. Filling this gap enables more interpretable ML models that align with chemical intuition.

### How this project addresses the gap

This project isolates feature contributions by comparing a 3D-GNN against traditional 2D descriptors on the QM9 dataset. By applying permutation importance and attention analysis, we will quantify the specific predictive signal of 3D conformation versus atom/bond types for dipole moments.

## Expected results

We expect 3D-equivariant GNNs to outperform 2D descriptors on dipole prediction, confirming that conformation carries significant signal. Feature attribution analysis will reveal that electronegative atom placement and bond angles contribute more to predictive variance than bond types alone. Statistical significance will be confirmed via paired t-tests on RMSE across cross-validation folds.

## Methodology sketch

- Download the QM9 dataset (134k molecules) from Figshare (DOI: 10.6084/m9.figshare.9981994) and filter to a random 20k subset to fit 7GB RAM.
- Preprocess data to extract 3D coordinates, atom types, and bond connectivity; generate standard descriptors (Morgan fingerprints, Coulomb matrices) for baseline.
- Implement a lightweight SchNet-style GNN using PyTorch Geometric (CPU-only mode) and train for 50 epochs with early stopping.
- Train a Random Forest baseline on traditional descriptors using the same train/test splits.
- Evaluate both models on a held-out test set using Mean Absolute Error (MAE) for dipole moments.
- Apply permutation importance to the GNN node embeddings and Random Forest features to rank structural contributions.
- Perform paired t-tests (α=0.05) comparing RMSE distributions between GNN and baseline across 5 random seeds.
- Visualize feature importance maps on representative molecules to correlate learned weights with chemical intuition.

## Duplicate-check

- Reviewed existing ideas: None identified in current project context.
- Closest match: N/A (No similar dipole-feature-interpretability projects found in context).
- Verdict: NOT a duplicate
