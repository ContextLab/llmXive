# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No `setup_dirs.py` script is present, and the required directories (`code/`, `data/`, `data/raw`, `data/processed`, `data/logs`, `tests/`, `artifacts/`, `figures/`) are not shown to exist. The claim lacks any tangible artifact to verify that the directory structure was created.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or related setup scripts were provided. Without these artifacts, the task of configuring ruff/flake8 and Black cannot be confirmed as done.
- `T007a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): The submission contains only the feature specifications and user stories; there is no `.env` file, configuration script, or documentation showing environment variable handling for API keys. Consequently, the required artifact for task T009 (environment configuration management) is missing.
- `T025b` (rejected 1x): declared artifact(s) missing/empty/invalid: figures/feature_importance.png
- `T030` (rejected 1x): No `quickstart.md` or `research.md` files were presented in the evidence, and there is no content indicating they were created or populated. The required documentation artifacts are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

