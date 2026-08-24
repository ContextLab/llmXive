# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T012a creates a config file but the verification step is missing. It says 'Note: Thresholds are chosen... verification of the resulting count occurs in T012b'. While T012b verifies the count, T012a itself lacks a direct verification step (e.g., 'Verify file exists and is valid YAML'). This is a granularity/verification gap that the atomizer might split, but it should be explicit here.
- T060 requires running the 'FULL flow-matching solver'. The task does not specify the exact command, script path, or arguments to invoke this solver. It assumes the implementer knows where the solver code is. This is not self-contained; the task must name the specific script (e.g., 'code/inference/full_solver.py') and arguments to be deterministic.
- T043 requires updating `state.yaml` key `validation_status`. The verification step says 'state and log reflect outcome'. It does not specify the exact key path in `state.yaml` (e.g., 'state.validation_status' vs 'state.metrics.validation_status'). This ambiguity prevents deterministic implementation of the state update logic.
- T009 (Implement Data Source Check) states: 'If both missing, fetch `voxceleb2` via `datasets.load_dataset`...'. This violates FR-019 and Constitution Principle I (Reproducibility) if the fetch logic does not strictly pin the dataset revision. While T005b mentions pinning, T009's verification only checks for file existence, not the *content* or *revision* of the fetched dataset. A task that fetches a dataset without verifying the revision hash against the pinned config silently relaxes the reproducibility constraint.
