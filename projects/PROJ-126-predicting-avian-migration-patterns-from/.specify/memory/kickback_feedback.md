# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan computes an effort covariate (`effort_covariate = number of complete checklists per cell‑year`) and then uses this covariate *only as a predictor* for the model (see Phase 1.3 and Phase 2). However, the target variable (first‑arrival week) is defined from raw cumulative counts of the same checklists without any effort adjustment. Because higher observer effort directly increases the chance of early detections, the effort covariate is *not independent* of the target definition. Including it as a predictor therefore creates a circular relationship: the model can improve performance by exploiting effort‑related signal rather than genuine environmental drivers (temperature/NDVI). This violates the scientific‑soundness requirement that predictors be independent of the way the outcome is constructed, and it undermines the validity of any inference about environmental effects.
