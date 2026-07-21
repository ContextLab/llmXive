# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The required output file `data/raw/golden_subset.json` does not exist, and the provided `generator.py` snippet is incomplete (truncated) so we cannot verify that it actually calls `verify_pairing` or produces data matching the specified schema. The task’s core deliverable is missing.
- `T015b` (rejected 1x): The repository contains `code/data/golden_set_generator.py`, but the script is incomplete (truncated) and the required output file `data/raw/human_annotated_subset.json` does not exist. Without a generated JSON containing ≥10 labeled traces, the task’s core requirement is unmet.
- `T012` (rejected 1x): The `goal_validator.py` uses the wrong ID regex (`\b(\w+\d+)\b` instead of the required `\b(\w+_\d+)\b`) and the expected output file `data/processed/static_constraints.json` is not present. Both the pattern specification and the required artifact are missing/incorrect.
- `T013` (rejected 1x): The repository contains `code/classification/state_validator.py`, which implements loading, comparison, and accuracy calculation, but the required input file `data/raw/human_annotated_subset.json` is absent, so the validator cannot be run against the golden data. Without this file (or a generated reconstruction), the task’s core requirement is unmet.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/classification_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

