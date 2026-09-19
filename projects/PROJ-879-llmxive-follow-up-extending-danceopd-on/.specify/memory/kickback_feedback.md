# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The provided `code/00_data_extraction.py` is incomplete (the core extraction and write‑to‑Parquet logic is truncated and not present), and the required output file `data/processed/teacher_routing_dataset.parquet` does not exist. Consequently the task’s requirement—to extract the four fields and stream them to the specified Parquet file—has not been fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

