# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006b` (rejected 1x): The provided `code/downloaders.py` does not contain any logic that uses `datasets.load_dataset` to fetch the OQMD data and write it as `data/raw/oqmd.parquet`; it only defines generic download utilities and is truncated. Moreover, the required output file `data/raw/oqmd.parquet` is absent. The task’s core requirement is therefore unmet.
- `T006d#1` (rejected 1x): The repository lacks the required `data/raw/mp.parquet` file, and the provided `code/downloaders.py` is truncated (e.g., incomplete `update_state_file` function) with no visible logic that uses `datasets.load_dataset('materials-project/mp', split='train')` or checks for an API key. Consequently the task’s core requirement—to download the Materials Project dataset to the specified path when a valid API key is present—is not satisfied. The implementer must add the MP download code and ensure the parquet file is created (or correctly handle missing API key).

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

