---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Composition on the Glass Transition Temperature of Chalcogenide Glasses

**Field**: Materials Science

## Research question

How do mean coordination number and chemical heterogeneity jointly determine the glass transition temperature in chalcogenide networks?

## Motivation

Accurate prediction of the glass transition temperature (Tg) is critical for designing chalcogenide glasses with stable thermal profiles for phase-change memory and infrared optics. While empirical rules exist, they fail to capture non-linear interactions between elemental substitutions and network rigidity. This project addresses the gap between physical constraint theory and data-driven modeling to enable targeted material synthesis without exhaustive experimental screening.

## Literature gap analysis

### What we searched

Queries included "chalcogenide glass Tg machine learning" and "glass transition temperature rigidity composition" across Semantic Scholar and arXiv. The search returned three primary records, two of which were directly on-topic for chalcogenide Tg modeling, while one addressed general materials discovery strategies.

### What is known

- [Accelerated Design of Chalcogenide Glasses through Interpretable Machine Learning for Composition Property Relationships (2022)](http://arxiv.org/abs/2211.00691v1) — Establishes that interpretable ML models can successfully map composition to properties in chalcogenide systems, validating the data-driven approach.
- [Variation of the glass transition temperature with rigidity and chemical composition (2005)](http://arxiv.org/abs/cond-mat/0510054v1) — Provides the physical constraint theory linking mean coordination number to Tg, offering a theoretical baseline for feature engineering.

### What is NOT known

Existing work demonstrates that ML works generally but lacks specific quantification of how chemical heterogeneity (beyond mean coordination) modulates Tg in novel compositions. There is no published benchmark evaluating the generalization error of gradient boosting models when extrapolating to unseen elemental combinations in this class of glasses.

### Why this gap matters

Filling this gap allows researchers to distinguish between topological constraints and chemical effects when tuning thermal stability. This distinction is necessary for accelerating the discovery of glasses that meet strict thermal requirements for photonic applications without costly trial-and-error synthesis.

### How this project addresses the gap

The project's methodology explicitly tests feature importance for heterogeneity descriptors using SHAP values, directly measuring the contribution of chemical variance alongside rigidity metrics. By evaluating generalization on held-out novel compositions, the model quantifies the specific predictive limits of current constraint-based assumptions.

## Expected results

The model will identify that chemical heterogeneity contributes significantly to Tg variance beyond mean coordination number alone. A gradient boosting regressor will achieve lower RMSE than linear baselines on held-out test sets, confirming non-linear interaction effects are present in the dataset.

## Methodology sketch

- Download the tabular dataset of chalcogenide compositions and Tg values from the supplementary repository of the 2022 study [1].
- Compute compositional descriptors including mean coordination number, electronegativity variance, and atomic radius variance for each sample.
- Split the data into training (80%) and testing (20%) sets stratified by chemical family to ensure generalization testing.
- Train a Gradient Boosting Regressor using scikit-learn on CPU with 5-fold cross-validation to tune hyperparameters.
- Apply SHAP (SHapley Additive exPlanations) analysis to quantify the contribution of each descriptor to Tg predictions.
- Compare model performance (RMSE, R²) against a linear baseline to confirm the presence of non-linear interactions.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None.
- Verdict: NOT a duplicate
