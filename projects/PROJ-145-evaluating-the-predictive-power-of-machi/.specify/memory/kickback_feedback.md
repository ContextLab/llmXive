# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required root directories (`code/`, `data/raw/`, `data/processed/`, `data/models/`, `tests/unit/`, `tests/integration/`, `specs/`) is provided; the implementer did not supply a directory listing or any files showing that these folders have been created. The task remains unfinished until the specified directories exist in the repository.
- `T001b` (rejected 1x): No evidence of any `__init__.py` files was provided; the implementer did not show the new directories or the empty files required by task T001b. The required artifacts are missing, so the task is not satisfied.
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., ruff settings, black configuration, pre‑commit hooks) are present in the provided evidence, so the required artifact for task T004 is missing.
- `T006` (rejected 1x): No `tests/` directory (or any subdirectories for unit and integration tests) is present in the repository, nor any files indicating that such a structure was created. The implementer provided no artifact matching the task requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

