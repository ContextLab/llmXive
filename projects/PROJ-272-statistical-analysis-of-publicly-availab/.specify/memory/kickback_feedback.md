# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file list was provided showing that the required folders (`code`, `data/raw`, `data/processed`, `data/interim`, `data/results`, `tests/unit`, `tests/contract`, `tests/integration`, `specs/001-statistical-cognitive-decline/contracts`) actually exist. Without concrete evidence of these paths, the task’s requirement is not satisfied.
- `T003` (rejected 1x): The submission contains no visible linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or any documentation showing that ruff/flake8 and Black have been set up. Without these artifacts, the task of configuring the tools is not satisfied.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T017` (rejected 1x): No code, configuration, or log files were provided that demonstrate the addition of logging for excluded records with specific reason codes, nor any evidence that the logging parses the cognitive status metadata extraction result. The required artifact (implemented logging logic) is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

