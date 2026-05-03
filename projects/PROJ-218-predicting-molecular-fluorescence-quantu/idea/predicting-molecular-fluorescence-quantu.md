---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Field**: chemistry

## Research question

Can a graph neural network trained on publicly available molecular structure and fluorescence quantum yield data achieve predictive accuracy (R² ≥ 0.7) comparable to experimental measurement uncertainty? Which molecular substructures contribute most strongly to fluorescence quantum yield variation?

## Motivation

Experimental determination of fluorescence quantum yield (FQY) requires specialized spectroscopy equipment and time-consuming sample preparation, creating a bottleneck in materials discovery for bioimaging, sensing, and optoelectronics applications. A machine learning surrogate model trained on existing public datasets could accelerate candidate screening and help identify structural motifs that enhance or suppress fluorescence efficiency.

## Related work

- [MECCH: Metapath Context Convolution-based Heterogeneous Graph Neural Networks (2022)](http://arxiv.org/abs/2211.12792v2) — Demonstrates heterogeneous graph neural networks for structural representation learning, relevant for encoding molecular bond types and atom environments in GNN architectures.
- [QTN-VQC: An End-to-End Learning framework for Quantum Neural Networks (2021)](http://arxiv.org/abs/2110.03861v3) — Explores quantum-inspired neural network frameworks, though current NISQ hardware constraints make classical GNNs more practical for this task.

## Expected results

A GNN model trained on curated FQY datasets should achieve R² ≥ 0.7 on held-out test molecules, with root mean squared error below 0.15 absolute quantum yield units. Feature attribution analysis (e.g., integrated gradients) will reveal which molecular fragments correlate with high or low fluorescence efficiency, providing actionable design rules for synthetic chemists.

## Methodology sketch

- Download the FluorDB or Zenodo-curated FQY dataset containing SMILES strings and experimental quantum yield values (target: N ≥ 500 molecules).
- Parse SMILES to molecular graphs using RDKit (Python), extracting node features (atom type, hybridization, formal charge) and edge features (bond type, conjugation).
- Implement a message-passing GNN with 3-4 graph convolution layers (e.g., GraphConv or GAT) using PyTorch Geometric or DGL, keeping model parameters under 5M to fit 7GB RAM.
- Split data 80/10/10 (train/validation/test) with scaffold-based splitting to ensure chemical diversity across splits.
- Train for ≤50 epochs with early stopping (patience=10) using Adam optimizer and mean squared error loss; log training curves.
- Evaluate on test set using R², RMSE, and MAE; compare against baseline linear regression on molecular fingerprints (ECFP4).
- Apply SHAP or integrated gradients to compute feature importance scores for top 20 most influential substructures.
- Generate 3-5 visualization figures: training convergence plot, parity plot (predicted vs. experimental FQY), and feature importance bar chart.
- Document all code, hyperparameters, and data preprocessing steps in a reproducible notebook for GitHub Actions execution.

## Duplicate-check

- Reviewed existing ideas: [N/A — no existing fleshed-out ideas provided in corpus].
- Closest match: None identified.
- Verdict: NOT a duplicate
