# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was presented showing that `code/` and `tests/` directories actually exist in the repository root (or contain any files). The implementer’s claim cannot be verified without such artifacts.
- `T001b` (rejected 1x): No evidence was provided showing that the `data/raw`, `data/processed`, and `data/models` directories actually exist in the repository root; the implementer’s claim is unsubstantiated. The required directory structure must be created and verified.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or CI workflow steps) were provided or referenced, so the required artifacts for configuring ruff/flake8 and Black are missing. The implementer must add the appropriate config files and ensure they are non‑empty and correctly set up.
- `T011` (rejected 1x): No evidence was provided showing that `tests/unit/` and `tests/integration/` directories (with non‑empty test files) actually exist in the repository. Without these artifacts, the task of setting up the unit and integration test structure is not satisfied. The next implementer should create the two directories and add appropriate placeholder test modules.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

