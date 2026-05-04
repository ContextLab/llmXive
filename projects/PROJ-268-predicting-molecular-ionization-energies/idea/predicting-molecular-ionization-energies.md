---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Ionization Energies with Graph Neural Networks

**Field**: chemistry

## Research question

Can a lightweight graph neural network trained on a public molecular dataset predict molecular ionization energies with accuracy comparable to quantum chemical methods, while reducing computational cost by orders of magnitude?

## Motivation

Accurate ionization energy prediction is essential for understanding chemical reactivity and spectroscopic behavior, but high-level quantum calculations are prohibitively expensive for large-scale virtual screening. Machine learning offers a potential acceleration, yet existing approaches often require specialized infrastructure or proprietary data. This project addresses the gap for a lightweight, reproducible GNN method that runs on standard compute resources while maintaining predictive accuracy.

## Related work

- [Machine learning of molecular electronic properties in chemical compound space (2013)](https://doi.org/10.1088/1367-2630/15/9/095003) — Pioneering work demonstrating ML can predict electronic properties from molecular descriptors with quantum-chemistry accuracy.
- [Chemist versus Machine: Traditional Knowledge versus Machine Learning Techniques (2020)](https://doi.org/10.1016/j.trechm.2020.10.007) — Reviews the transition from chemical heuristics to ML approaches in materials discovery.
- [Social Influence Prediction with Train and Test Time Augmentation for Graph Neural Networks (2021)](http://arxiv.org/abs/2104.11641v1) — Demonstrates GNN data augmentation strategies that could transfer to molecular graph preprocessing.
- [MECCH: Metapath Context Convolution-based Heterogeneous Graph Neural Networks (2022)](http://arxiv.org/abs/2211.12792v2) — Shows heterogeneous GNN architectures for complex structural data, relevant to multi-atom molecular graphs.

## Expected results

We expect the GNN to achieve mean absolute error (MAE) below 0.3 eV on held-out test molecules, comparable to DFT-level accuracy. Performance will be measured against a baseline of semi-empirical quantum methods, with statistical significance confirmed via paired t-test on test predictions. Success requires consistent accuracy across diverse functional groups, not just on training-set analogues.

## Methodology sketch

- Download QM9 dataset (https://figshare.com/articles/dataset/qm9/1224189) containing ~134k molecules with computed ionization energies.
- Preprocess SMILES strings into molecular graphs using RDKit (Python package, CPU-only).
- Split data 80/10/10 into train/validation/test sets with scaffold-based splitting to prevent data leakage.
- Implement Message-Passing Neural Network (MPNN) using PyTorch Geometric (lightweight, CPU-compatible).
- Train for ≤50 epochs with early stopping on validation loss; batch size ≤64 to fit 7GB RAM.
- Evaluate MAE, RMSE, and R² on test set; compare against DFTB semi-empirical baseline.
- Perform ablation study on graph augmentation (from arxiv.2104.11641) to assess robustness.
- Generate feature importance visualization via gradient-based attribution.
- All code and trained weights packaged in single GitHub repo for reproducibility.
- Target runtime: ≤4 hours end-to-end on 2 CPU cores.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None identified.
- Verdict: NOT a duplicate
