# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The provided `download.py` is truncated and does not contain the full implementation (e.g., the dataset loading line is incomplete, no code to convert to Parquet, no fallback wget logic, and no checksum writing after a successful download). Additionally, the expected output files `data/raw/uspto_raw.parquet` and `data/results/download_checksum.txt` are missing. The task’s requirements are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

