# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): No `utils/checkpointing.py` file or its contents are presented; therefore the required functions (`save_state`, `load_state`, `delete_checkpoint`) with cross‑platform locking and atomic writes are not verified to exist. The task’s deliverable is missing.
- `T014` (rejected 1x): The provided `code/checksum_datasets.py` is truncated (e.g., the `update_datasets_csv_with_checksums` function is cut off and there is no entry‑point that actually invokes the checksum computation and writes `data/checksums.csv`). Moreover, the expected output file `data/checksums.csv` is absent, indicating the script has not been fully implemented or executed. The missing code and lack of the CSV output mean the task requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

