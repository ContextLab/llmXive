# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The required output file `data/processed/cleaned_issues.csv` is missing (and thus no checksum can be generated), so the core part of the task is not satisfied despite the presence of a validation report. The implementer must create the cleaned dataset at the specified path (and compute its checksum) before the task can be considered complete.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: data/logs/preprocessing.log
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/outlier_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

