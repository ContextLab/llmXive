---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Field**: chemistry

## Research question

Can lightweight graph neural networks trained on public molecular datasets predict reaction yields or rate constants with accuracy comparable to low-level quantum methods, without requiring GPU acceleration?

## Motivation

Computational screening of molecular reactivity typically relies on density functional theory (DFT), which is computationally expensive and often requires specialized hardware. This research addresses the gap for rapid, CPU-based screening methods that leverage publicly available data. Success would enable resource-constrained environments (e.g., GitHub Actions runners) to perform preliminary reactivity assessments for catalyst discovery.

## Related work

- [Graph Neural Networks for Databases: A Survey (2025)](http://arxiv.org/abs/2502.12908v2) — Provides foundational context on handling graph-structured data within database systems, relevant for managing large molecular repositories.
- [MECCH: Metapath Context Convolution-based Heterogeneous Graph Neural Networks (2022)](http://arxiv.org/abs/2211.12792v2) — Demonstrates heterogeneous GNN architectures for complex structural data, informing the design of molecule-specific graph layers.
- [A Neural Network-Evolutionary Computational Framework for Remaining Useful Life Estimation of Mechanical Systems (2019)](http://arxiv.org/abs/1905.05918v1) — Illustrates general neural network frameworks for prediction tasks, serving as a methodological baseline for regression-based property estimation.

## Expected results

We expect to achieve a Pearson correlation coefficient (R) greater than 0.7 between predicted and actual reactivity values on a held-out test set. The measurement will confirm the viability of CPU-based GNN inference for preliminary chemical screening, with evidence supported by RMSE comparisons against baseline linear models.

## Methodology sketch

- Download the QM9 dataset (subset of 10,000 molecules) via HuggingFace Datasets (`huggingface/datasets`) using `wget` or Python API.
- Preprocess SMILES strings into graph structures (nodes=atoms, edges=bonds) using RDKit (CPU mode).
- Construct a 2-layer Graph Convolutional Network (GCN) using PyTorch Geometric, enforcing CPU-only execution (`device='cpu'`).
- Train the model for 50 epochs with early stopping to fit within the 6-hour GitHub Actions job limit.
- Evaluate performance on a 20% held-out test set using Mean Squared Error (MSE) and Pearson correlation.
- Apply a paired t-test to compare prediction errors against a baseline Random Forest model to assess statistical significance.
- Log all artifacts (model weights, metrics) to the repository for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: None (similarity sketch: N/A).
- Verdict: NOT a duplicate
