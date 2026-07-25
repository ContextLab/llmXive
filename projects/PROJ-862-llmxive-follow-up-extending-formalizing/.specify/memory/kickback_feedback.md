# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The repository lacks the required data files (`data/processed/baseline_vectors.csv` and the output `filtered_pairs_input_drift.csv`). The provided `check_input_drift` function is incomplete (truncated), has a different signature than specified, and does not demonstrate saving the filtered pairs to the CSV with the exact column names. Additionally, the singleton is named `_GLOBAL_SBERT` instead of the required `GLOBAL_SBERT`. These missing/incorrect elements must be added for the task to be considered complete.
- `T026` (rejected 1x): No code, configuration, or log files were provided that implement “Add logging for sweep progress and memory usage.” The evidence contains only a feature specification unrelated to logging, and there are no artifacts showing the required logging functionality. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

