# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): The execution log does confirm a fresh run (`python -m code.main --mode single ...`) with exit 0 and top eigenvalue 2.901642355091, matching the claimed value. However, the task also claims "JSON validated; logs and checksum created," and no evidence on disk shows a results JSON file, a checksum of the raw matrix, or any validation output — the run's stdout is empty and only a stderr log line exists. The implementer must produce and show the actual JSON results artifact and the matrix checksum to satisfy the reproducibility/validation requirements.
- `T006` (rejected 1x): Requested task execution failed; rerun successfully: code/analysis/threshold_fit.py exit=1

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

