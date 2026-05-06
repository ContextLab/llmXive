---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

**Field**: chemistry

## Research question

How do molecular structural features determine aqueous solubility variations across diverse pharmaceutical compounds?

## Motivation

Aqueous solubility is a primary determinant of drug bioavailability, yet experimental measurement remains slow and resource-intensive. Current computational models often rely on hand-crafted descriptors that may miss complex topological patterns. This project addresses the gap in understanding how graph-structural representations capture the physicochemical drivers of solubility compared to traditional methods.

## Related work

- [Enhancing molecular property prediction with quantized GNN models (2025)](https://doi.org/10.1186/s13321-025-00989-3) — Establishes that quantized GNNs can efficiently predict water solubility among other molecular properties without significant accuracy loss.
- [Graph Neural Networks for Predicting Solubility in Diverse Solvents using MolMerger incorporating Solute-solvent Interactions (2024)](http://arxiv.org/abs/2402.11340v1) — Demonstrates the application of GNNs specifically for solubility prediction while incorporating solute-solvent interaction features.
- [A review of methods for the calculation of solution free energies and the modelling of systems in solution (2015)](https://doi.org/10.1039/c5cp00288e) — Provides foundational context on the thermodynamic principles governing solution free energies relevant to solubility modeling.
- [Machine learning methods in chemoinformatics (2014)](https://doi.org/10.1002/wcms.1183) — Reviews the historical diffusion of machine learning algorithms into chemical modeling, establishing the baseline for modern predictive approaches.

## Expected results

The GNN-based model is expected to achieve lower root mean squared error (RMSE) on test data compared to random forest baselines using Morgan fingerprints. A statistically significant improvement (p < 0.05 via paired t-test) would confirm that graph topology encodes additional solubility-relevant information beyond fixed descriptors. Null results would suggest that simple structural descriptors are sufficient for this specific property range.

## Methodology sketch

- Download the ESOL (Delaney) dataset from the MoleculeNet benchmark repository (publicly available CSV).
- Preprocess SMILES strings into molecular graphs using RDKit, extracting atom and bond features.
- Implement a Message Passing Neural Network (MPNN) using PyTorch Geometric configured for CPU-only execution.
- Split data into 80% training, 10% validation, and 10% test sets with stratification on logS values.
- Train the model for 100 epochs with early stopping based on validation loss.
- Train a baseline Random Forest model using Morgan fingerprints on the same data splits.
- Evaluate both models on the test set using RMSE and R-squared metrics.
- Perform a paired t-test on the absolute prediction errors to assess statistical significance.
- Generate feature importance visualizations (e.g., attention weights) to interpret topological contributions.
- Archive code and model weights in a public repository for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A.
- Verdict: NOT a duplicate
