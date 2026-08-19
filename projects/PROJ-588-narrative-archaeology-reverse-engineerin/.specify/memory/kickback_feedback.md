# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No project directory or file structure was presented; the implementer supplied only the specification text without any actual folders, README, source code layout, or other artifacts that would constitute a created project structure. Consequently the required deliverable is missing.
- `T002` (rejected 1x): The implementer only supplied a feature specification and no concrete project initialization artifacts (e.g., a repository, `pyproject.toml`, `requirements.txt`, or any Python files). There is no evidence that a Python 3.11 project was created or that the listed dependencies (transformers, pandas, numpy, openneuro‑cli) were added. The required initialization step is missing.
- `T003` (rejected 1x): No flake8 or black configuration files (e.g., `.flake8`, `pyproject.toml` with black settings, or a pre‑commit hook) were provided, so the required linting/formatting setup is missing. The implementer’s claim cannot be verified without those artifacts.
- `T009` (rejected 1x): No code, configuration, or documentation showing an error‑handling layer that detects motion‑artifact subjects, skips them, and logs the errors is present. The required artifact (implementation of the skip‑on‑artifact and logging infrastructure) is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

