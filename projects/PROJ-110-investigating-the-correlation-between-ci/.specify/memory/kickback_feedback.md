# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Potential double-correction for PMI. Phase 5 fits 'Expression ~ ... + PMI', but research.md (Section 2) and spec.md (FR-031) mandate 'linear regression residualization' of expression for PMI. Residualizing the dependent variable and then including the same variable as a covariate in the model is statistically unsound and leads to over-correction.
- Category error in correlation analysis. The plan states 'select Spearman/Pearson -> fit mixed-effects model' to 'aggregate these correlations'. A mixed-effects model is fit to raw data (or rank-transformed data for Spearman equivalence), not to correlation coefficients. One does not 'aggregate correlations' via a mixed-effects model; the model itself estimates the global fixed effect.
