# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T001 lists 'Create subdirectories: data/raw, data/results, code, tests/unit, tests/contract, contracts' but the phrasing 'contracts (root level)' is ambiguous regarding the relative path. It should explicitly state 'Create directory: contracts/ at repository root' to ensure the file paths in T009a-c match the directory structure.
- Task T035 performs a sensitivity analysis sweeping pruning thresholds and recalculating the tipping point for each sweep. However, it fails to define how the final 'tipping point' (SC-004) is selected or reported if these multiple recalculations yield different values. This creates a silent ambiguity in the success criterion: the Spec requires a single 'tipping point' threshold measured against the PLR breakpoint, but the task produces multiple candidates without a selection rule, violating the measurability of SC-004.
