# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009b` (rejected 1x): The provided `code/data/real_data_validator.py` is truncated (ends with `logging.inf`) and lacks a runnable entry point that counts studies, raises a warning/error when N < 10, and writes the required `data/processed/real_data_status.json`. Moreover, the status JSON file is missing entirely. The task’s core functionality and output artifact are not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

