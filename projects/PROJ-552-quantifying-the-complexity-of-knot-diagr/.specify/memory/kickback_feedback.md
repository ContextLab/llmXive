# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'writing'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- SC-013 claims 'All metrics use explicit quantitative thresholds' but lists unquantified terms: 'null percentage is minimal, format pass rate is high, duplicates are absent'. This is an internal contradiction within the criterion that should be resolved for consistency.

## MAINTAINER DECISION — round 2 (resolve the last 2 spec concerns)

1. SC-013 self-contradicts: it claims "All metrics use explicit
   quantitative thresholds" but then lists three UNquantified terms.
   Quantify them verbatim and keep the rest of SC-013 intact:
   - "null percentage is minimal" → "null percentage ≤ 5% per field"
   - "format pass rate is high" → "format pass rate ≥ 99%"
   - "duplicates are absent" → "duplicate records = 0 (0%)"
2. FR-005 vs SC-011 threshold inconsistency: FR-005 says residuals
   "≥ 2 standard deviations from the global mean" but SC-011 (correctly,
   per regression practice) says "from the fitted trend". Change FR-005
   to "≥ 2 standard deviations from the fitted trend (model predictions)"
   so both match. Residuals are measured from model predictions, never
   the global mean.

After these, the spec carries no unquantified design targets and no
internal threshold contradictions. Do not reintroduce any.
