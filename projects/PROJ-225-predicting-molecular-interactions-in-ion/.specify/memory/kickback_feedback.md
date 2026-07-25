# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015a` (rejected 1x): The provided `code/data_ingestion.py` does not contain a `calculate_partial_charges_internal_only(df)` implementation (the visible portion shows only download utilities and no such function), and the required `data/processed/internal_consistency_checks.parquet` file is absent. Both the function and its saved output are missing, so the task is not fulfilled.
- `T017e` (rejected 1x): The provided `code/data_ingestion.py` excerpt does not contain a `write_unified_dataset(df, path)` function, and the expected output file `data/processed/unified_dataset.parquet` is absent from the repository. Consequently the required implementation and artifact are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

