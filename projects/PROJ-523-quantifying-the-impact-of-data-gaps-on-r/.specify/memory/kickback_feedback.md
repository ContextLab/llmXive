# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-004 allows 'Fisher matrix analysis OR a pre-computed likelihood grid'. Task T028b explicitly discards the pre-computed grid option. While a choice, the spec's Assumptions section notes pre-computed grids are a valid fallback if convergence fails. The plan lacks a task to generate or verify the existence of a pre-computed grid as a backup, creating a single point of failure if the on-the-fly Fisher matrix fails.
- T049 requires refactoring T029b to move the 'Minimum 30 Valid Realizations' check. It fails to specify the exact error handling mechanism (e.g., 'raise StatisticalPowerError') as a concrete code artifact to be written, relying on the implementer to infer the exception class and message format.
