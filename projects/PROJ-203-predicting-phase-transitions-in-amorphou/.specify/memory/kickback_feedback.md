# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: code/utils/timeout_enforcer.py
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: code/models/train.py, data/processed/final_dataset.parquet, docs/reports/confusion_matrix.png
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: docs/reports/collinearity_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

