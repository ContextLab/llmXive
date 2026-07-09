# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T015 (US1) implements propensity score matching using 'block-level metrics and repo-level covariates (stars, age)'. However, T010-T014 (US1) only extract block-level metrics (complexity, LOC) and tag blocks. The 'repo-level covariates' (stars, age) are NOT extracted in any US1 task. T010 fetches repos but does not explicitly extract 'stars' and 'age' into a structured format consumable by T015. T011 clones repos but filters by activity, not extracting metadata for matching. The artifact 'matched_pairs.csv' (T015 output) requires these covariates, but no upstream task in Phase 3 produces them. This is a missing producer before consumer violation.
