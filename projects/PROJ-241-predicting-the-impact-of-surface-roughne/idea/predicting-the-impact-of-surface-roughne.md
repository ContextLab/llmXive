---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Surface Roughness on Tribological Properties

**Field**: materials science

## Research question

How can surface topography parameters (e.g., Sa, Sq, Ssk) combined with material properties be used to predict the coefficient of friction and wear rate in tribological contacts using machine learning regression models?

## Motivation

Surface roughness significantly impacts friction and wear in tribological contacts, but quantifying this relationship across diverse material pairings remains challenging. Existing literature demonstrates the potential of data-driven approaches for material property estimation, yet a focused ML pipeline for roughness-to-tribology prediction is lacking. This project addresses that gap by developing a reproducible model using public datasets, which could accelerate the design of surfaces with optimized wear resistance without requiring extensive experimental trials.

## Related work

- [Mining experimental data from Materials Science literature with Large Language Models: an evaluation study (2024)](http://arxiv.org/abs/2401.11052v3) — Demonstrates LLMs can extract structured tribological data from scientific documents, supporting automated dataset curation for this project.
- [Efficient Estimation of Material Property Curves and Surfaces via Active Learning (2020)](http://arxiv.org/abs/2010.06896v1) — Provides methodology for estimating material property surfaces using active learning, applicable to modeling roughness-tribology relationships.
- [Fiber-Reinforced Polymer Composites: Manufacturing, Properties, and Applications (2019)](https://doi.org/10.3390/polym11101667) — Illustrates how manufacturing-induced surface characteristics affect composite material performance, relevant for surface feature extraction.

## Expected results

A regression model achieving R² > 0.7 on held-out test data for coefficient of friction prediction, with feature importance analysis identifying 3-5 dominant roughness parameters. Cross-validation on at least 200 data points from public repositories will provide statistical evidence of model generalizability across material pairings.

## Methodology sketch

- Download surface roughness and tribology datasets from OpenML (ID: 42123) and NIST Materials Data Repository (https://www.nist.gov/mml/mmd/material-data-portal)
- Extract surface parameters (Sa, Sq, Ssk, Sku, Sp, Sv) using Python's `scikit-surface` or `pySurf` libraries
- Clean and normalize data; handle missing values via median imputation
- Split dataset into 70% training / 15% validation / 15% test sets
- Train baseline regression models (Linear Regression, Random Forest, Gradient Boosting) using `scikit-learn`
- Perform hyperparameter tuning via 5-fold cross-validation on validation set
- Evaluate models using R², MAE, and RMSE metrics on test set
- Conduct feature importance analysis using SHAP values to identify dominant roughness parameters
- Generate visualization plots (feature importance bar chart, predicted vs. actual scatter)
- Document all code and results in a reproducible Jupyter notebook

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified.
- Verdict: NOT a duplicate
