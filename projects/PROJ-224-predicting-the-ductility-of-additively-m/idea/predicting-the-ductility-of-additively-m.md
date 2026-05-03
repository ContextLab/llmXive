---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys

**Field**: materials science

## Research question

Can machine learning models trained on publicly available process-parameter and mechanical-property datasets accurately predict the ductility (elongation to failure) of additively manufactured nickel-based superalloys?

## Motivation

Additively manufactured nickel-based superalloys offer significant advantages for high-temperature engineering applications, but unpredictable ductility remains a major barrier to certification and adoption. Current literature focuses heavily on microstructure characterization and crack susceptibility, with limited work on quantitative ductility prediction from process parameters. Establishing a predictive model could accelerate material optimization and reduce expensive experimental trial-and-error.

## Related work

- [Revealing 3D Strain and Carbide Architectures in Additively Manufactured Ni Superalloys](http://arxiv.org/abs/2602.15729v1) — Provides foundational microstructural analysis of columnar grains and cellular sub-grain structures that directly influence ductility in AM Ni superalloys.
- [Process parameter sensitivity of the energy absorbing properties of additively manufactured metallic cellular materials](http://arxiv.org/abs/2212.00438v1) — Demonstrates how process parameters affect mechanical properties in AM metals, establishing precedent for parameter-property modeling.
- [On the influence of alloy composition on the additive manufacturability of Ni-based superalloys](http://arxiv.org/abs/2109.15274v1) — Examines composition and processing-induced crack formation, highlighting the complexity of AM Ni-alloy property prediction.
- [Simultaneously enhanced strength and ductility for 3D-printed stainless steel 316L by selective laser melting](https://doi.org/10.1038/s41427-018-0018-5) — Shows successful ML-informed optimization of ductility in AM metals, providing methodological precedent for this project.

## Expected results

A random forest or gradient boosting model achieving R² ≥ 0.65 on held-out test data would indicate meaningful process-ductility relationships. Cross-validation will confirm model generalizability across different alloy compositions and laser parameter ranges. Feature importance analysis should identify the most influential process parameters (e.g., laser power-to-speed ratio) for ductility optimization.

## Methodology sketch

- Download open AM superalloy datasets from HuggingFace Datasets (search "additive manufacturing superalloy") and Materials Project API; target ≥200 samples with process parameters and elongation-to-failure values.
- Clean data: remove entries with missing ductility values, standardize units (laser power in W, speed in mm/s, hatch spacing in µm).
- Engineer features: calculate volumetric energy density (power/(speed×hatch×layer thickness)) and dimensionless process ratios.
- Split data: 70% training, 15% validation, 15% test, stratified by alloy composition family.
- Train random forest baseline (scikit-learn, max_depth=10, n_estimators=100) and gradient boosting (XGBoost, early_stopping_rounds=20).
- Perform 5-fold cross-validation on training set to tune hyperparameters; record mean absolute error (MAE) and R² for each fold.
- Apply permutation importance to rank features by contribution to ductility prediction accuracy.
- Generate partial dependence plots for top 3 features to visualize non-linear process-ductility relationships.
- Run statistical significance test: compare model R² against null model (mean prediction) using F-test (α=0.05).
- Output: model weights, feature importance table, and uncertainty bounds for all predictions (95% confidence intervals).

## Duplicate-check

- Reviewed existing ideas: None in current project corpus (first submission in this field).
- Closest match: N/A (no prior fleshed-out ideas in materials science/AM superalloys domain).
- Verdict: NOT a duplicate
