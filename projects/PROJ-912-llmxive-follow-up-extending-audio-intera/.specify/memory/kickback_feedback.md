# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): The `loader.py` file is present but its content (truncated) shows only utility functions; there is no implementation of `datasets.load_dataset(..., streaming=True)`, on‑the‑fly filtering, recovery strategy, parquet generation, or the watchdog logic. Moreover, the required output file `data/processed/subtle_cue_subset.parquet` is missing. The task’s core requirements are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

