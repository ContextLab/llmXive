# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005c` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): The repository lacks the required `data/raw/bronze.parquet` file and the state YAML still contains `data_raw_bronze: null`, indicating the hash was never written. Moreover, the provided `code/ingest.py` is truncated, never calls `compute_sha256` after download, and does not invoke `update_state_artifact_hash` to record the checksum. The critical integrity steps are therefore not implemented.
- `T007b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/bronze.parquet
- `T063` (rejected 1x): The required artifact `data/raw/bronze.parquet` does not exist on disk, so the download logic and fallback handling have not been demonstrated. The task’s primary output is missing, indicating the implementation is not complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

