---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines

**Field**: materials science

## Research question

Can we accurately predict the glass transition temperature (Tg) of amorphous polymer blends using only compositional descriptors and Explainable Boosting Machines (EBMs), and which compositional features most strongly influence Tg?

## Motivation

Glass transition temperature is a critical thermal property determining polymer material performance, but experimental determination is time-consuming and resource-intensive. This project addresses the gap between existing ML approaches for polymer property prediction and the need for interpretable models that reveal structure-property relationships to guide material design.

## Related work

- [Predicting Properties of Polymer Materials Using Machine Learning Methods](https://www.semanticscholar.org/paper/a7d1e46569f494c7bf1d758bd9d7d3afa6e11df) — Establishes the feasibility of ML-based polymer property prediction and highlights limitations of traditional experimental methods.
- [Prediction of Reduced Glass Transition Temperature using Machine Learning (2020)](http://arxiv.org/abs/2005.08872v1) — Demonstrates data-driven modeling approaches for glass transition temperature prediction in materials science.
- [Interpretable and Explainable Machine Learning for Materials Science and Chemistry (2021)](http://arxiv.org/abs/2111.01037v2) — Provides the theoretical foundation for using EBMs to achieve model interpretability in materials discovery workflows.
- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems (2025)](http://arxiv.org/abs/2512.05895v2) — Shows recent advances in compositional ML for glass property prediction, though focused on alloys rather than polymers.
- [Recent advances and applications of machine learning in solid-state materials science (2019)](https://doi.org/10.1038/s41524-019-0221-0) — Reviews ML tool adoption in materials science and validates the computational approach for property prediction tasks.

## Expected results

We expect to achieve Tg prediction with R² ≥ 0.70 on held-out test data using compositional descriptors alone. Feature importance analysis from the EBM will identify specific functional groups and elemental ratios that drive Tg variations, providing actionable design guidelines for polymer synthesis.

## Methodology sketch

- Download polymer Tg dataset from Polymer Genome (https://polymergenome.org) and NIST Chemistry WebBook (https://webbook.nist.gov) using wget/curl scripts.
- Extract compositional descriptors: elemental ratios, functional group percentages, and molecular weight averages from SMILES strings using RDKit (CPU-only).
- Preprocess data: handle missing values via median imputation, normalize features using StandardScaler, split into 70/15/15 train/validation/test sets.
- Train Explainable Boosting Machine (EBM) using interpretml package (pip install, no GPU required).
- Perform 5-fold cross-validation on training set to tune regularization hyperparameters (λ, interaction_depth).
- Evaluate model performance using R², RMSE, and MAE metrics on validation and test sets.
- Apply permutation importance and partial dependence plots to extract feature importance rankings.
- Conduct statistical significance testing (t-test, α=0.05) on top-5 features to confirm their contribution to Tg prediction.
- Generate SHAP-style interaction plots to visualize non-linear feature effects on predicted Tg.
- Document all code, data sources, and reproducibility scripts in a public GitHub repository.

## Duplicate-check

- Reviewed existing ideas: [none provided in current session].
- Closest match: N/A (no existing ideas to compare against).
- Verdict: NOT a duplicate
