# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/contract/test_schema_validation.py
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/integration/test_pipeline.py
- `T012` (rejected 1x): The `data/processed/cleaned_compositions.csv` file does not exist, and the shown portion of `code/01_data_ingestion.py` is truncated before any logic that normalizes/rejects compositions and writes the filtered DataFrame to that path. Consequently, the required validation and output generation are not demonstrably implemented.
- `T013` (rejected 1x): The required log file `data/artifacts/imputation_log.txt` does not exist, and the provided excerpt of `code/01_data_ingestion.py` shows no implementation of KNN imputation, row‑dropping on failure, or logging of the imputation rate. The task’s core functionality and artifact are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

