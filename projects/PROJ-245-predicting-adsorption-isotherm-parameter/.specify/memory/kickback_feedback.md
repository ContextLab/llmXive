# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015b` (rejected 1x): The `impute_pore_volume` function is present but the source is truncated before the imputation and exclusion‑logging logic, and the required `data/validation/exclusion_log.json` file does not exist, so the hierarchical imputation and failure‑logging requirements are not fully demonstrated.
- `T014d` (rejected 1x): The repository lacks the required `data/validation/missing_descriptors_report.json` file, and the provided `code/data/descriptors.py` does not show a function that reads the three `missing_descriptors_*.json` files and writes a merged report. Without the output file or merging logic, the task is not fulfilled.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/validation/null_model_comparison.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

