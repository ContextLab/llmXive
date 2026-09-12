# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing or proof of the required folders (`data/raw/`, `data/processed/`, `code/models/`, `code/analysis/`, `code/utils/`, `code/config/`, `tests/contract/`, `tests/unit/`, `tests/integration/`) is provided, so we cannot verify that the project structure was created. The implementer must supply evidence (e.g., a tree view, screenshots, or a script output) showing the directories exist.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or CI workflow steps invoking these tools) are present in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied.
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/deduplicated.csv
- `T014` (rejected 1x): No code, script, log file, or dataset was provided to demonstrate that rows with missing permeability values are being filtered out and that a specific log entry such as “Missing target variable” is emitted. Without these artifacts, the requirement cannot be verified. The implementer must supply the ingestion/processing script (or notebook) and example output logs showing the exclusion and reason logging.
- `T016` (rejected 1x): No code, configuration, or documentation was provided showing that logging for exclusion reasons and exclusion‑rate statistics has been added. The required artifact (e.g., updated ingestion script with logging statements, log file examples, or a description of the new logging behavior) is missing, so the task is not satisfied.
- `T017` (rejected 1x): No code, script, or documentation implementing `streaming=True` dataset loading was provided, nor any test showing memory usage stays < 2 GB or that the pipeline fails when the dataset exceeds the limit. The required artifact (streaming logic with enforced memory constraint and failure behavior) is missing.
- `T017b` (rejected 1x): No verification logic, script, or test output was provided to show that the final dataset is checked for ≥500 (or 2000) unique compounds and that an error is raised when the count is below the target. The required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

