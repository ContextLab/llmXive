---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Viscosity from Structural Features with Machine Learning

**Field**: chemistry

## Research question

Can machine learning models trained on molecular structural descriptors (fingerprints, graph features) accurately predict the viscosity of small organic molecules within ±20% of experimental values?

## Motivation

Viscosity measurements are time-consuming and expensive, creating a bottleneck in solvent selection and process optimization for chemical manufacturing. A reliable prediction model would accelerate materials screening while leveraging existing public datasets of molecular properties without requiring new experimental data collection.

## Related work

- [Machine Learning Harnesses Molecular Dynamics to Discover New μ Opioid Chemotypes](http://arxiv.org/abs/1803.04479v1) — Demonstrates ML applications in computational chemistry for property prediction, establishing precedent for structure-property relationship modeling.
- [Physics-Inspired Interpretability Of Machine Learning Models](http://arxiv.org/abs/2304.02381v2) — Highlights importance of explainable ML models, relevant for understanding which molecular features drive viscosity predictions.
- [MerLin: A Discovery Engine for Photonic and Hybrid Quantum Machine Learning](http://arxiv.org/abs/2602.11092v2) — Explores systematic empirical exploration of ML in molecular discovery, though focused on quantum approaches beyond current scope.

Note: Literature search did not return viscosity-specific ML studies; existing work focuses on drug discovery and interpretability rather than physical property regression.

## Expected results

A random forest or gradient boosting model achieving R² ≥ 0.7 on held-out test molecules would confirm structural descriptors contain sufficient signal for viscosity prediction. Root mean square error (RMSE) below 0.3 log(η) would indicate practical utility for solvent screening. Feature importance analysis should identify molecular weight, polarity, and branching as dominant predictors.

## Methodology sketch

- **Data acquisition**: Download viscosity datasets from PubChem Property Database and OpenChemLib (publicly available CSV/JSON formats); target ≥500 molecules with experimental viscosity values.
- **Feature engineering**: Compute molecular fingerprints (ECFP4, MACCS keys) and graph descriptors (molecular weight, logP, polar surface area) using RDKit (Python package, CPU-friendly).
- **Data preprocessing**: Split data 80/20 train-test; handle missing values via median imputation; normalize numerical features using StandardScaler.
- **Model selection**: Train random forest, gradient boosting (XGBoost), and linear regression baselines; limit trees to ≤500 and depth to ≤15 to stay within 7GB RAM.
- **Hyperparameter tuning**: Grid search with 5-fold cross-validation on training set; limit parameter combinations to ≤50 to fit within 6h runtime.
- **Evaluation**: Compute R², RMSE, MAE on test set; generate residual plots and feature importance rankings.
- **Validation**: Apply model to external test set (if available) to assess generalization; document all random seeds for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate
