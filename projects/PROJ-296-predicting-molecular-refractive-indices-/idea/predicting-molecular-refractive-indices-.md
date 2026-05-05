---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

**Field**: chemistry

## Research question

Can lightweight graph neural networks (GNNs) trained on public molecular graph data predict refractive indices with mean absolute error (MAE) below 0.05, using only CPU-based inference?

## Motivation

Refractive index is a fundamental optical property critical for pharmaceutical formulation and material design, yet standard determination relies on slow quantum mechanical calculations. Graph-based machine learning offers a potential speedup, but feasibility on resource-constrained environments (e.g., GitHub Actions free tier) remains unproven. This project addresses the gap between high-accuracy quantum methods and efficient predictive modeling for early-stage screening.

## Related work

- [Dynamic Molecular Graph-based Implementation for Biophysical Properties Prediction (2022)](http://arxiv.org/abs/2212.09991v1) — Demonstrates the efficacy of GNNs in predicting biophysical properties, establishing a baseline for graph-based molecular property regression.

## Expected results

The GNN model is expected to achieve an MAE < 0.05 on a held-out test set of organic molecules, outperforming simple linear empirical correlations. Statistical significance will be confirmed via paired t-test against baseline empirical predictions on the same test set. Evidence will be sufficient if cross-validation variance is < 10% of the mean error.

## Methodology sketch

- **Data Acquisition**: Download a pre-processed CSV of molecular SMILES and refractive index values from the NIST Chemistry WebBook (https://webbook.nist.gov) or a curated Zenodo mirror (search query: "molecular refractive index dataset").
- **Data Preprocessing**: Use RDKit (CPU version) to convert SMILES strings to molecular graphs; filter for molecules with molecular weight < 500 Da to reduce complexity.
- **Dataset Split**: Randomly split data into 80% training, 10% validation, 10% testing; ensure no structural overlap between splits.
- **Model Architecture**: Implement a 3-layer Message Passing Neural Network (MPNN) using PyTorch Geometric; disable GPU acceleration flags to enforce CPU execution.
- **Training Configuration**: Limit training to 50 epochs with early stopping (patience=10) to fit within the 6-hour GitHub Actions time limit; batch size set to 32 to respect 7GB RAM constraints.
- **Computation**: Calculate Mean Absolute Error (MAE) and Root Mean Square Error (RMSE) on the test set; store predictions in a local CSV artifact.
- **Statistical Validation**: Perform a paired t-test comparing model predictions against calculated empirical estimates (e.g., Lorentz-Lorenz) to assess improvement significance.
- **Visualization**: Generate a parity plot (Predicted vs. Actual) and save as PNG; ensure file size < 5MB for artifact storage.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: N/A.
- Verdict: NOT a duplicate
