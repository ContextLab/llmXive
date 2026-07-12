# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T025b (Implement validation logic) depends on T025a (Create registry). This is correct. T025b requires the registry file to exist.
- T027 (Implement power analysis) depends on T020 (Validate output schema) and T026 (Apply correction). T027 requires the *output* of T023 (correlation results) to perform power analysis. The current dependencies T020 and T026 are incorrect. T027 should depend on T023 (to ensure correlation results exist) and T009 (for correction logic if needed). T020 is a validation step, not a data generation step.
- T032 (Implement age stratification) depends on T031 (Implement regression.py). T032 is a logic step within the regression analysis. It should depend on the *execution* of T031. The current dependency T031 -> T032 is correct for implementation order, but T032 requires the *output* of T031 to be executed.
- T033 (Implement plots.py) depends on T032 (Age stratification). T033 generates plots. T032 stratifies data. T033 requires the *output* of T032 (stratified data) to generate plots. This dependency is correct.
- Task T032 'Implement age stratification logic... and output warning flag' is ambiguous. It should be 'Create data/results/regression_summary.json containing a 'warnings' array; if N < 15 for Older group, append 'Low Power for Older Group' to the array. Verify file exists and contains warning'.
