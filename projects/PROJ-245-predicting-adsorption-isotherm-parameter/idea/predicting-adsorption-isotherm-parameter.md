---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Adsorption Isotherm Parameters from Molecular Features

**Field**: chemistry

## Research question

Can machine learning regression models accurately predict key adsorption isotherm parameters (e.g., Henry's constant, Freundlich exponent, Langmuir capacity) for gas adsorption on solid surfaces using only molecular descriptors of the adsorbate and basic physicochemical properties of the adsorbent?

## Motivation

Adsorption isotherm parameters are critical for designing materials for gas storage, separation, and catalysis, yet determining them experimentally is time-consuming and resource-intensive. A data-driven approach using publicly available adsorption datasets and molecular descriptors could accelerate material screening and reduce experimental burden. This addresses the gap between high-throughput computational screening and experimental validation in adsorbent design.

## Related work

- [Simple isotherm equations to fit type I adsorption data (2009)](http://arxiv.org/abs/0911.2012v2) — Proposes simplified models for fitting experimental type I adsorption isotherm data on microporous adsorbents, establishing baseline fitting procedures.
- [AIM: A User-friendly GUI Workflow program for Isotherm Fitting, Mixture Prediction, Isosteric Heat of Adsorption Estimation, and Breakthrough Simulation (2025)](http://arxiv.org/abs/2504.20713v2) — Presents a GUI-based software tool for adsorption isotherm fitting and related calculations, highlighting the need for accessible computational workflows.
- [Adsorption from Binary Liquid Solutions into Mesoporous Silica: A Capacitance Isotherm on 5CB Nematogen/Methanol Mixtures (2021)](http://arxiv.org/abs/2102.06908v1) — Demonstrates capacitance-based measurement of adsorption isotherms for liquid-phase systems, relevant for multi-component adsorption modeling.
- [Aromatics and Cyclic Molecules in Molecular Clouds: A New Dimension of Interstellar Organic Chemistry (2021)](http://arxiv.org/abs/2103.09608v1) — Provides molecular property data for aromatic compounds, which could inform molecular descriptor calculations for adsorbates.
- [Flexible metal–organic frameworks (2014)](https://doi.org/10.1039/c4cs00101j) — Reviews flexible MOF structures and their adsorption characteristics, offering adsorbent property data for model training.

## Expected results

The ML model should achieve R-squared ≥0.7 for Henry's constant prediction and ≤20% mean absolute error for Freundlich exponent estimation on held-out test data. Performance will be validated through k-fold cross-validation and comparison against baseline linear regression. Success will be demonstrated by identifying feature importance rankings that align with known physicochemical principles of adsorption.

## Methodology sketch

- Download publicly available adsorption isotherm datasets from NIST Adsorption Database or HuggingFace Datasets (e.g., MOF adsorption benchmarks via DOI: 10.1038/s41597-020-00736-0)
- Calculate molecular descriptors for adsorbates using RDKit (molecular weight, polar surface area, polarizability, H-bond donors/acceptors, van der Waals volume)
- Extract adsorbent properties from dataset metadata or compute from crystallographic data (pore volume, surface area, functional group counts)
- Preprocess data by filtering for type I isotherms and removing entries with missing parameters or inconsistent units
- Train baseline linear regression model and compare against random forest and gradient boosting regressors (scikit-learn)
- Perform 5-fold cross-validation with hyperparameter tuning (grid search over 10 combinations, max 30 minutes total)
- Evaluate models using R-squared, RMSE, and MAE on test set (10% holdout)
- Apply SHAP analysis to identify most influential molecular and adsorbent features
- Generate correlation heatmaps between predicted and experimental parameters using matplotlib
- Document all code and data versions in a GitHub repository with a requirements.txt file

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified.
- Verdict: NOT a duplicate
