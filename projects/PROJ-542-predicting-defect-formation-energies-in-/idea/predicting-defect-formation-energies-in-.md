---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Defect Formation Energies in Perovskites with Machine Learning

**Field**: materials science

## Research question

How do compositional descriptors (e.g., atomic radii, electronegativity, oxidation states) correlate with defect formation energies across different perovskite crystal structures, and can this relationship be modeled to enable rapid screening of novel compositions?

## Motivation

Defect formation energies govern the electronic and optoelectronic properties of perovskite materials critical for solar cell applications. First-principles density functional theory (DFT) calculations are accurate but computationally expensive, limiting exploration of the vast compositional space. A data-driven model trained on existing DFT datasets could accelerate materials discovery by identifying promising perovskite compositions for experimental validation.

## Related work

- [Simple Structural Descriptor Obtained from Symbolic Classification for Predicting the Oxygen Vacancy Defect Formation of Perovskites (2022)](https://www.semanticscholar.org/paper/53d9eda84e4932bfd3206df3a83fca01f73ad550) — Demonstrates interpretable ML formulas for predicting oxygen vacancy defect formation, establishing precedent for descriptor-based approaches.
- [Oxygen Vacancy Formation Energy in Metal Oxides: High-Throughput Computational Studies and Machine-Learning Predictions (2023)](https://www.semanticscholar.org/paper/82f407a49b3450e31aa7fbc0901626e0338116ab) — Shows defect formation energy can be predicted via ML from high-throughput DFT data, directly supporting this project's feasibility.
- [Defect formation in CsSnI$_3$ from Density Functional Theory and Machine Learning (2024)](https://www.semanticscholar.org/paper/9a883e7d1d1a7f3e917c82f42934fbd924f11582) — Provides case study on Sn-based perovskite defect modeling, offering domain-specific validation of ML approaches for perovskites.
- [Crystal Graph Convolutional Neural Networks for an Accurate and Interpretable Prediction of Material Properties (2018)](https://doi.org/10.1103/physrevlett.120.145301) — Establishes graph-based ML architecture for crystalline materials, relevant for feature representation strategy.
- [Comparative analysis of machine learning approaches on the prediction of the electronic properties of perovskites: A case study of ABX3 and A2BB’X6 (2021)](https://www.semanticscholar.org/paper/e1ec7856302507c00424644fd67a4f5fa82e19f0) — Benchmarks multiple ML methods on perovskite properties, informing algorithm selection.

## Expected results

We expect to identify a subset of compositional descriptors that explain ≥70% of variance in defect formation energies across perovskite compositions, validated via cross-validation RMSE <0.5 eV against held-out DFT data. A positive result would demonstrate that simple descriptors can substitute for expensive DFT calculations in screening workflows, while a null result would indicate defect energies require more complex structural representations beyond composition alone.

## Methodology sketch

- Download defect formation energy dataset from Materials Project (API: https://next-gen.materialsproject.org/, specific defect entries filtered by perovskite structure type)
- Extract compositional features: atomic radii, Pauling electronegativity, oxidation states, and valence electron counts for A, B, and X sites using pymatgen
- Construct training set: ~500–1000 perovskite compositions with DFT-calculated defect energies (oxygen vacancies as primary target)
- Train baseline ML models (Random Forest, Gradient Boosting) using scikit-learn on CPU with 5-fold cross-validation
- Evaluate model performance via RMSE, MAE, and R² against held-out test set (20% of data)
- Apply statistical significance test (paired t-test) comparing ML predictions vs. DFT ground truth on test set (α=0.05)
- Generate feature importance ranking to identify which compositional descriptors most strongly predict defect formation energy
- Visualize results with scatter plots (predicted vs. actual) and feature importance bar charts
- Document all code and data preprocessing steps in reproducible Jupyter notebook

## Duplicate-check

- Reviewed existing ideas: [none provided in input corpus]
- Closest match: none identified (literature search confirms this specific focus on compositional descriptors for perovskite defect energies is not saturated)
- Verdict: NOT a duplicate
