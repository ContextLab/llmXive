# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/`, `tests/`, `state/`) being present on disk is provided; the artifact list is empty, so the project structure has not been demonstrated.
- `T001a` (rejected 1x): No directory listings or file system evidence were provided showing that the required folders (`code/`, `data/raw/`, `data/processed/`, `data/features/`, `tests/`, `state/projects/`) actually exist; without such artifacts the claim cannot be confirmed.
- `T001c` (rejected 1x): No evidence was provided that a `tests/` directory (with sub‑directories `contract/`, `integration/`, and `unit/`) actually exists in the repository; the response contains only the task description and no file listings or screenshots showing the required directory structure. The implementer must add the specified directories (and optionally placeholder test files) to satisfy the task.
- `T001d` (rejected 1x): declared artifact(s) missing/empty/invalid: PROJ-122-identifying-structure-property-relations.yaml
- `T003` (rejected 1x): The implementer provided only the feature specification and no actual linting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or CI integration scripts). There is no evidence that flake8 or Black have been installed, configured, or invoked, so the task requirement is not met.
- `T004` (rejected 1x): No `.gitignore` file or pytest configuration (e.g., `pytest.ini`, `pyproject.toml` with `[tool.pytest]`, or `conftest.py`) was presented in the evidence, so the required artifacts are missing. The task cannot be considered done until these files are created and contain appropriate content.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

