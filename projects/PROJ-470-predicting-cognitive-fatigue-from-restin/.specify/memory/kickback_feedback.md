# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The provided `download_manifest.json` reports `"status": "success"` but contains an empty `variables_found` list and a participant count of 0, indicating the script never validated or found the required fatigue rating columns. The `download.py` file is truncated and does not show the required structural/participant validation, error‑exit logic, or writing of the exclusion log beyond an empty header. Consequently the implementation does not fulfill the task’s validation, exclusion, and output requirements.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

