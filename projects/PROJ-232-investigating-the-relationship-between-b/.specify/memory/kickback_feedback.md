# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (`src/`, `tests/`, `specs/`) is provided; the implementer did not supply any file listings or screenshots showing that these folders exist and contain appropriate placeholder files. The task remains undone.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.flake8` or `.ruff.toml` files, or a setup script) are present in the provided evidence, so the task of configuring ruff/flake8 and Black has not been demonstrated. The required artifacts are missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): No `.env` file, loading script, or documentation of environment variable handling was provided; the implementer gave no code or file evidence that configuration management for API keys and data paths has been set up. The required artifact is missing.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/download.py
- `T011b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/download.py, data/data_gap_report.md
- `T012c` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/preprocess.py, data/preprocessing/run_log.json
- `T012d` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- `T012e` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/preprocess.py, data/preprocessing/run_log.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

