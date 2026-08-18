# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No `plan.md` file or any directory structure under `projects/PROJ-205-.../` is present; the required project scaffold was not provided. The task’s core deliverable is missing.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) or setup instructions were provided, so the requirement to configure ruff/flake8 and black is not satisfied.
- `T009` (rejected 1x): No evidence was provided that the `data/raw/` and `data/processed/` directories actually exist in the repository (or that they contain any placeholder files). The implementer’s claim lacks the required filesystem artifacts, so the directory structure setup cannot be confirmed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

