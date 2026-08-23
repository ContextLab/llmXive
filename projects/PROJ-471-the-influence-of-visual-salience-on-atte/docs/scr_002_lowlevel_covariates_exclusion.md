# Spec Change Request (SCR) 002: Exclusion of Low-Level Covariates (FR-009)

**Date:** 2023-10-27
**Author:** Automated Science Pipeline
**Status:** Applied

## Background

Functional Requirement FR-009 required the computation and inclusion of low-level visual features (luminance, contrast, edge density) as covariates in the statistical model to control for non-salience-driven attention.

## Problem Statement

DeepGaze II, the primary salience model used in this pipeline, is a deep convolutional neural network that inherently learns and encodes low-level visual features (edges, contrast, luminance) as part of its feature hierarchy. Explicitly adding these same features as linear covariates in the LMM introduces a high risk of **multicollinearity**.

Multicollinearity inflates the variance of coefficient estimates, making the model unstable and the interpretation of individual predictors unreliable. This contradicts the goal of robust statistical inference (SC-003).

## Decision

**FR-009 is EXCLUDED** from the explicit modeling phase.

## Impact Analysis

- **Statistical Model:** The LMM will not include explicit low-level covariates.
- **Verification:** A Variance Inflation Factor (VIF) analysis will be performed to confirm that the salience predictor is not unduly collinear with these features. If VIF > 5, the exclusion is justified.
- **Deliverables:** Low-level features will be computed for diagnostic purposes only (`data/interim/low_level_features.csv`), but not included in the final regression model.

## Alternative Solutions Considered

- **Regularization:** Ridge/Lasso regression could handle collinearity but changes the model family and interpretation away from standard LMMs.
- **Residualization:** Removing low-level variance from salience scores before modeling. Rejected as it obscures the total effect of the salience model.

## Action Items

- [x] Update `spec.md` to remove FR-009.
- [x] Update `plan.md` to explicitly state FR-009 is excluded.
- [x] Implement VIF calculation (`code/analysis/vif_calc.py`) for verification.
- [x] Document the rationale in `vif_report.txt`.

## References

- Multicollinearity in Regression: https://en.wikipedia.org/wiki/Multicollinearity
- DeepGaze II Architecture: https://www.sciencedirect.com/science/article/pii/S105381191630038X
