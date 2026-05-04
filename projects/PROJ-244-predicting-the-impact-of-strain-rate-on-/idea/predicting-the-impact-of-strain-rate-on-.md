---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Strain Rate on the Yield Strength of Metals

**Field**: materials science

## Research question

How does strain rate quantitatively affect the yield strength of common metallic alloys, and can machine learning models trained on public tensile test data generalize across different alloy compositions and testing conditions?

## Motivation

Understanding strain-rate sensitivity is critical for materials selection in dynamic loading applications (e.g., crashworthiness, impact resistance), yet existing empirical models are often alloy-specific and lack generalizability. This project addresses the gap by building data-driven models that capture strain-rate effects across diverse alloy families, enabling more reliable predictions for engineering design under varying loading rates.

## Related work

TODO — lit-search returned no results.

## Expected results

We expect to find a positive correlation between strain rate and yield strength across most metallic alloys, with the magnitude of this effect varying by alloy family (e.g., aluminum vs. steel vs. titanium). A random forest or gradient boosting model should achieve R² > 0.7 on held-out test data, with feature importance analysis revealing strain rate as a significant predictor alongside composition and grain size.

## Methodology sketch

- Download tensile test datasets from NIST Materials Data Repository (https://www.nist.gov/materials-data) and OpenML (https://www.openml.org/search?type=data&search=metal+yield)
- Parse and clean data: extract yield strength, strain rate, alloy composition, grain size, temperature, and testing protocol fields
- Handle missing values through imputation or sample exclusion; standardize numerical features
- Split data into train/validation/test sets (70/15/15) stratified by alloy family
- Train baseline models (linear regression) and ML models (random forest, gradient boosting)
- Evaluate using R², MAE, and RMSE on test set; compare cross-validation performance across alloy types
- Perform feature importance analysis to quantify strain rate sensitivity relative to other predictors
- Generate partial dependence plots showing yield strength vs. strain rate for representative alloy groups

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: N/A
- Verdict: NOT a duplicate
