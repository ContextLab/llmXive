# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan does not clarify whether permutation importance is evaluated on the held‑out test set or on the same data used to train the final model. Computing importance on the training data can inflate importance scores and constitute data leakage.
- Permutation importance scores are assessed with a two‑tailed t‑test assuming normality of the importance distribution. Permutation importance values are often skewed and may not satisfy the t‑test’s assumptions, so the reported p‑values could be invalid. A non‑parametric test (e.g., permutation‑based significance) would be more appropriate.
