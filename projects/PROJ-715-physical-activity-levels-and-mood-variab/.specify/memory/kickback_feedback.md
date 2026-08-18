# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003a` (rejected 1x): No `.flake8` file in the `code/` directory is presented, nor any excerpt of its contents showing the required `[flake8]` section with `max-line-length = 88` and `ignore = E203, E266, W503`. Without this artifact, the task requirement is not satisfied.
- `T011` (rejected 1x): The repository lacks the required `data/raw/bronze.parquet` file, and the `parse_step_logs()` implementation is incomplete (it only begins parsing and is truncated, and does not itself load the parquet file). Consequently the task’s core requirement—to load the bronze parquet and produce daily step totals—is not met.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/daily_aggregates.csv, schema.yaml
- `T019b` (rejected 1x): No artifact (e.g., verification script output, log, or documentation) was provided showing that the `mood_std` column in `daily_aggregates.csv` was checked and confirmed to be unchanged and available for downstream analyses. Without such evidence, the task requirement is not satisfied.
- `T034b` (rejected 1x): No `docs/` files were presented; there is no evidence that API documentation for `analysis.py` or a Data Dictionary for `daily_aggregates.csv` were created or updated. The required documentation artifacts are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

