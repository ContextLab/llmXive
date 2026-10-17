# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-004 and US-2 acceptance scenario 2 mandate Type I error estimation 'by shuffling group labels multiple times with a fixed random seed' on the filtered datasets. T005/T007 instead estimate it exclusively on simulated null data (real data used only for shape estimation). The plan's methodological correction is defensible, but the spec was never amended, so the tasks silently relax a stated FR. Amend FR-004/US-2 to codify the simulated-null method (and note the permutation-based label assignment) rather than leaving the contradiction.
