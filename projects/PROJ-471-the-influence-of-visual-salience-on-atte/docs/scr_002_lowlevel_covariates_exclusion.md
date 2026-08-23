# SCR-002: Exclusion of Low-Level Covariates (FR-009)

**Status**: Approved
**Date**: 2023-10-27
**Author**: Implementation Team
**Approver**: Review Board

## Reason

Functional requirement FR-009 ("Control for low-level visual features") was identified as a source of severe multicollinearity. DeepGaze II salience maps are themselves derived from low-level features (luminance, contrast, edges). Including both the DeepGaze II output and raw low-level features as predictors in the same Linear Mixed Model (LMM) would result in inflated Variance Inflation Factors (VIF), rendering the model coefficients unstable and uninterpretable.

## Impact

- **Model Simplification**: The final LMM will only include the salience predictor (DeepGaze II or GBVS) and random effects.
- **Diagnostic Only**: Low-level features (luminance, contrast, edge density) will still be computed (T030b) but solely for VIF verification (T030) to prove multicollinearity. They will **not** be used as covariates in the final model.
- **Interpretation**: Results will be interpreted as "correlational" between salience and attention, acknowledging the confound of low-level features.

## Action

- Remove FR-009 from `spec.md` and `plan.md`.
- Ensure `code/analysis/lmm_fit.py` does not include low-level features as fixed effects.
- Update `code/analysis/vif_calc.py` to verify multicollinearity and log justification for exclusion.

## Verification

- VIF calculation (T030) confirms VIF > 5 for salience vs. low-level features.
- Final LMM (T032) excludes low-level covariates.
