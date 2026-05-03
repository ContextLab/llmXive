---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Yield Strength of Steel Alloys from Composition and Heat Treatment Parameters

**Field**: Materials Science

## Research question

Can machine learning regression models, trained on publicly available datasets of steel alloy compositions and heat treatment parameters, accurately predict yield strength (R² > 0.8) for unseen alloy compositions?

## Motivation

Experimental determination of yield strength is time-consuming and costly; accurate ML predictions could accelerate materials discovery by screening candidate compositions in silico. This project addresses the gap in generalizable models that account for complex interactions between elemental ratios and thermal processing schedules.

## Related work

- [Post-Heat Treatment Design of High-Strength Low-Alloy Steels Processed by Laser Powder Bed Fusion](http://arxiv.org/abs/1910.09939v3) — Demonstrates process-structure-property relations in HSLA steels, relevant for feature engineering heat treatment parameters.
- [Microstructural evolution of a low-alloy steel / nickel superalloy dissimilar metal weld during post-weld heat treatment](http://arxiv.org/abs/1911.12223v1) — Provides context on how post-weld heat treatment alters microstructure and mechanical properties in low-alloy steels.
- [Statistical analysis of the material, geometrical and imperfection characteristics of structural stainless steels and members](http://arxiv.org/abs/2010.14777v2) — Offers statistical frameworks for analyzing structural steel characteristics, supporting the validation methodology.

## Expected results

The model is expected to achieve a coefficient of determination (R²) above 0.8 on a held-out test set, confirming that composition and heat treatment are dominant predictors. Feature importance analysis will likely identify carbon content and cooling rate as top contributors, providing physical interpretability.

## Methodology sketch

- **Data Acquisition**: Download tabular steel alloy datasets (composition, heat treatment, yield strength) from the NIST Materials Data Repository (https://www.nist.gov/mml/materials-databases) or equivalent open Zenodo records via `wget`.
- **Preprocessing**: Clean missing values, normalize temperature/cooling rate features, and encode categorical heat treatment types (e.g., quenching, tempering).
- **Feature Engineering**: Generate interaction features for elemental ratios (e.g., C/Mn, Cr/Ni) and derived thermal parameters (e.g., cooling rate × holding time).
- **Model Selection**: Train baseline Linear Regression, Random Forest, and XGBoost regressors using `scikit-learn` (CPU-only mode).
- **Validation**: Perform 5-fold cross-validation to assess generalization; limit dataset size to <50k rows to ensure execution within 7 GB RAM.
- **Evaluation**: Compute RMSE, MAE, and R²; generate SHAP plots for feature interpretability.
- **Hardware Constraints**: Ensure all computation runs on 2 CPU cores within 6 hours; avoid large model grids or deep learning.

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None.
- Verdict: NOT a duplicate
