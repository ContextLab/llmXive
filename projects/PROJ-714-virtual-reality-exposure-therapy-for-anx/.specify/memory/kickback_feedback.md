# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan proposes using a 'custom implementation' of the DerSimonian-Laird estimator in Python if `statsmodels` lacks REML. While computationally feasible, relying on a custom implementation for the primary random-effects model introduces a high risk of implementation error (e.g., incorrect variance weighting) compared to using a peer-reviewed, widely validated library (like `metafor` in R or `statsmodels` if verified). The methodology lacks a validation step comparing the custom implementation against a gold-standard reference before production use.
- FABRICATED-RESULT signal — projects/PROJ-714-virtual-reality-exposure-therapy-for-anx/specs/001-virtual-reality-exposure-therapy-for-anx/plan.md: self-declared fabricated metric — “…mple correction; no simulated/placeholder results in final artifacts.   **Scal…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
- FABRICATED-RESULT signal — projects/PROJ-714-virtual-reality-exposure-therapy-for-anx/specs/001-virtual-reality-exposure-therapy-for-anx/plan.md: self-declared fabricated metric — “…tly forbids the generation of placeholder results. 1.  **Data Strategy**: The…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
