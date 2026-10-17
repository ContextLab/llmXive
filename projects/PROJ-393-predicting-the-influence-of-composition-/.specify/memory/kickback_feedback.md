# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T006 specifies output 'data/processed/alloys_raw.csv' but does not declare which imputation method is implemented. spec.md:FR-002 acceptance scenario 2 mandates 'mean imputation is applied, with a documented imputation rate <15%', while plan.md:Phase 1.2 describes 'MICE imputation' with a rule 'if >50% of a row is missing, perform listwise deletion; otherwise, use MICE'. These contradict. T006 must explicitly state which strategy is implemented and why, or the spec/plan must be aligned first.
