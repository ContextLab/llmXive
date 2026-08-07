# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T030` (rejected 1x): The provided `robustness_curve.py` only loads a CSV, extracts metadata, and builds a correlation list; it never reads `correlation_data.json`, performs the >10 % AUC drop detection, or writes `data/processed/breaking_point.json`. Moreover, the required `breaking_point.json` file is absent. The task’s core functionality is therefore not implemented.
- `T032` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/robustness_curve.png, data/processed/sensitivity_report.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

