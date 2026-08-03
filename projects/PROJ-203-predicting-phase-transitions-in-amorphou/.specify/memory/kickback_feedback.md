# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/final_dataset.parquet
- `T017` (rejected 1x): The required dataset `data/processed/final_dataset.parquet` does not exist, so the training script cannot actually load the crystallization labels. Moreover, the provided portion of `code/models/train.py` is truncated before any classifier training or confusion‑matrix‑saving logic, so it’s unclear whether those steps are implemented. Both the essential input file and the explicit saving of the confusion matrix are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

