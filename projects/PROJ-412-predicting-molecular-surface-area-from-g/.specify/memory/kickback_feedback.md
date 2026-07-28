# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): The repository contains a populated `pyproject.toml` with Black configuration, but the required `.ruff.toml` file is absent, so the linting tool configuration is not fully provided as the task demanded.
- `T015` (rejected 1x): The provided `preprocess.py` only defines helper functions and does not contain the chunked processing loop, failure‑rate check, or code that writes `data/processed/conformer_config.json` and `failure_report.csv`. Both required output files are missing from the repository. Consequently the task’s core requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

