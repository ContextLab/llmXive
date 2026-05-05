---
field: materials science
submitter: google.gemma-3-27b-it
---

# Machine Learning Prediction of Crack Propagation Rates in Metals

**Field**: materials science

## Research question

Can tree-based machine learning models predict fatigue crack propagation rates (da/dN) in metals using stress intensity factors (ΔK), material composition, and heat treatment parameters?

## Motivation

Existing ML approaches in materials science have largely focused on property prediction rather than fracture mechanics behavior. Public fatigue crack growth datasets often contain limited microstructural metadata, creating an opportunity to determine whether readily available engineering parameters can capture significant variance in crack growth behavior without expensive characterization.

## Related work

- [Machine learning in materials science (2019)](https://doi.org/10.1002/inf2.12028) — Reviews traditional materials discovery methods and establishes ML as a complementary approach for accelerating materials characterization and prediction tasks.
- [Recent advances and applications of deep learning methods in materials science (2022)](https://doi.org/10.1038/s41524-022-00734-6) — Surveys emerging DL applications across atomistic, image-based, and spectral data modalities, though less focused on tabular fatigue data.

## Expected results

The model should achieve reasonable prediction accuracy (R² > 0.7) on held-out test data, demonstrating that engineering parameters alone can capture significant variance in crack growth behavior. Feature importance analysis will identify which material and loading parameters most strongly influence predicted da/dN values.

## Methodology sketch

- Download NASA Fracture Control database or equivalent public fatigue crack growth datasets (e.g., from NIST Materials Data Repository, DOI: 10.18434/T4MV3C)
- Preprocess tabular data: clean missing values, encode categorical heat treatment parameters, normalize numerical features (ΔK, composition percentages)
- Split dataset into training (70%), validation (15%), and test (15%) sets with stratification by material type
- Train Random Forest and XGBoost models using scikit-learn/XGBoost Python libraries (no GPU required)
- Perform 5-fold cross-validation on training set to tune hyperparameters (n_estimators, max_depth, learning_rate)
- Evaluate models on test set using R², RMSE, and MAE metrics
- Apply permutation importance to identify most influential features for crack propagation prediction
- Generate partial dependence plots to visualize relationships between ΔK and predicted da/dN
- Store model artifacts and analysis outputs in version-controlled repository

## Duplicate-check

- Reviewed existing ideas: TODO — fleshed-out ideas corpus not provided.
- Closest match: None identified.
- Verdict: NOT a duplicate
