# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The repository lacks a `run_ingestion(peak_files)` function in `code/main.py` and the required `data/processed/ingestion_summary.json` file does not exist, so the specified summary JSON is never generated. The current code only shows a partially‑implemented `run_ingestion_pipeline` stub and no logic that creates the required keys or validates cell types.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

