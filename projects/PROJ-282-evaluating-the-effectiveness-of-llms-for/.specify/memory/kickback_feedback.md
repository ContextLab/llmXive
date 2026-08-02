# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure was presented in the evidence; the required folders (`src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `state/`) are not shown to exist or contain any files. The implementer must create and provide this project hierarchy.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or any evidence of ruff/black setup were provided; the claim lacks the required artifacts.
- `T009d` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T011` (rejected 1x): The provided `src/data/download.py` contains placeholder URLs and incomplete/fake logic for the NIST Juliet fetch, and there is no evidence that it implements the required primary‑fallback flow, writes `fallback_state.json`, or logs errors to `data/logs/error.log`. Moreover, the expected output files (`vuldeepecker.parquet`, `bigvul_c.parquet`, `bigvul_js.parquet`) and the log files are missing, indicating the script has not successfully performed the required downloads. The task therefore remains unfinished.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/preprocess.py, data/processed/predictions.csv, data/processed/features.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

