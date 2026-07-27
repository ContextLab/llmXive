# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory `projects/PROJ-504-evaluating-the-impact-of-variable-select/` or its subfolders (`code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/integration/`) was provided. The implementer must create this folder hierarchy and ensure each subdirectory exists and is non‑empty (or at least present).

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

