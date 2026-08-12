# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The required `data/processed/graphs_with_features.parquet` file does not exist, and the provided `code/data/preprocess.py` excerpt shows only setup and 3‑D conformer generation code—there is no visible implementation of 2‑D atom‑type/hybridization/charge features, molecular‑weight calculation, the >100‑atom filter, logging of excluded molecules, or writing the parquet file with the specified columns. The task’s core requirements are therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

