---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

**Field**: materials science

## Research question

Can machine learning models trained on publicly available polymer adhesion datasets predict the effect of surface treatment parameters (e.g., plasma power, exposure time, chemical concentration) on interfacial adhesion strength?

## Motivation

Surface treatments are routinely used to improve polymer-substrate bonding in aerospace, biomedical, and electronics manufacturing, but treatment selection remains largely empirical. A predictive model would reduce trial-and-error in process optimization and accelerate materials development for applications requiring reliable interfacial strength.

## Related work

TODO — lit-search returned no results.

## Expected results

We expect to identify treatment parameters that account for ≥50% of variance in adhesion strength across polymer-substrate pairs. Model performance will be measured using cross-validated R² and root-mean-square error (RMSE), with statistical significance assessed at p < 0.05.

## Methodology sketch

- Download polymer adhesion datasets from public repositories (e.g., NIST Materials Data Repository, Zenodo polymer adhesion datasets, HuggingFace Materials Science datasets) via `wget`/`curl`.
- Extract features: surface treatment type, power (W), exposure time (s), chemical concentration (%), polymer surface energy (mJ/m²), substrate roughness (nm).
- Preprocess data: handle missing values via median imputation, normalize numerical features, encode categorical treatment types.
- Split dataset: 70% training, 15% validation, 15% test with stratified sampling by treatment type.
- Train regression models: Random Forest, Gradient Boosting, and Linear Regression using scikit-learn.
- Tune hyperparameters via grid search (≤50 parameter combinations to fit within 6h GHA runtime).
- Evaluate using R², RMSE, and MAE on held-out test set.
- Apply SHAP analysis to identify most influential treatment parameters.
- Perform statistical validation: 5-fold cross-validation with permutation test (n=1000) to confirm model generalizability.
- Generate figures: feature importance plots, predicted vs. actual scatter plots, residual analysis (matplotlib/seaborn).

## Duplicate-check

- Reviewed existing ideas: N/A (initial flesh-out).
- Closest match: N/A.
- Verdict: NOT a duplicate.
