# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan includes FR-014 to validate distal CRE-Gene pairing via 'motif overlap or chromatin looping'. However, the statistical model (FR-005) does not explicitly incorporate the *strength* of this validation as a weight or filter in the regression. If a CRE has a weak motif match but passes the filter, it is treated identically to a strong match. This introduces noise into the predictor variable, reducing the power to detect the true effect. The methodology should either weight the predictor by motif score or restrict the analysis to high-confidence pairs only.
