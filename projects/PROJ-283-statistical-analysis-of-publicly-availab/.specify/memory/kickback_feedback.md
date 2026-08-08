# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008e` (rejected 1x): The repository lacks the required `data/raw/selected_ids.txt` file, and `src/data/download.py` does not implement the specified `retry_fetch_with_backoff` function, does not use `datasets.load_dataset(..., streaming=True)`, nor raise a `DataFetchError` on failure. The current code relies on `requests` and is incomplete/truncated, so the task’s core requirements are not satisfied.
- `T017` (rejected 1x): The `src/data/process.py` file shown does not contain a `save_inclusion_metrics` implementation (the excerpt ends before any such function). Moreover, the required `data/results/inclusion_metrics.json` file is absent. Both the function and the output file are missing, so the task requirements are not met.
- `T018` (rejected 1x): The provided `src/main.py` is truncated and does not show the logic that writes the validated DataFrame to `data/processed/games.parquet` or exits with code 1 on validation failure. Moreover, the required `data/processed/games.parquet` file is absent, so the script’s successful execution cannot be confirmed. The implementation must include the final save step, proper exit‑code handling, and the generated parquet file must exist.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

