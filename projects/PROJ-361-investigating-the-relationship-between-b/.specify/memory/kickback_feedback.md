# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No linting, formatting, or type‑checking configuration files (e.g., .flake8, pyproject.toml/black settings, mypy.ini) or any evidence of them being set up is present. The required artifacts to demonstrate that flake8, black, and mypy are configured are missing.
- `T004` (rejected 1x): No SQLite schema, SQL script, or code defining the required `subjects` and `files` tables with the specified columns was provided. The implementer’s claim lacks any tangible artifact demonstrating that the metadata registry has been set up.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

