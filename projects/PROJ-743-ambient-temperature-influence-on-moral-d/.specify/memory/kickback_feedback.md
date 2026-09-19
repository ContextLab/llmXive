# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): Both required files `data/raw/era5_full.parquet` and `data/raw/moral_machine.csv.gz` are missing, so the validation gate cannot verify their existence. The task’s core requirement is not satisfied.
- `T011` (rejected 1x): No code, configuration, or log files were provided showing that a logging infrastructure has been created to write data quality logs and model diagnostics to `results/logs/`. Without such artifacts, we cannot confirm the requirement has been met. The implementer must add the logging setup (e.g., Python logging config, log file creation, and example log entries) and ensure the `results/logs/` directory contains the generated logs.
- `T014` (rejected 1x): No pytest configuration files, test scripts, or documentation for CPU‑only execution and stratified sampling were provided; the claim lacks any tangible artifact demonstrating that the unit‑test framework has been set up as required.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

