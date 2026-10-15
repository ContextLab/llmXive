# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): The `code/utils/io.py` module exists, but its `save_parquet` function forces the use of the `pyarrow` engine, which is not available (ImportError shown in the test logs). Consequently the unit tests `test_save_and_load_parquet` and `test_sha256_checksum_and_verification` both fail, so the required I/O helpers do not reliably create and read Parquet files as specified. The logger module passes its tests. Fix the I/O helpers (e.g., make `pyarrow` optional or use a fallback engine) and ensure the tests pass.
- `T005` (rejected 1x): Requested task execution failed; rerun successfully: code/ingestion/download_ace.py exit=1; code/ingestion/download_noaa.py exit=1

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

