# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019b` (rejected 1x): declared artifact(s) missing/empty/invalid: scripts/verify_raw_integrity.py
- `T025` (rejected 1x): No `03_model_training.py` file or its contents were provided; without the script we cannot verify that model training, baseline model creation, or any of the required functionality (training 3‑5 models per dataset, saving predictions, etc.) has been implemented. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

