# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of a `src/`, `tests/`, or `data/` directory (or any files within them) was provided; the only material shown is a feature specification, not the required project structure. The implementer must create and show the three top‑level directories with appropriate placeholder files to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or CI integration scripts are present in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

