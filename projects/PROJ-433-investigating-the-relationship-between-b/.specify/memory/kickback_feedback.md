# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or other evidence were provided to show that the required folders (`data/raw`, `data/processed`, `data/results`, `code/`, `tests/`, `state/`) actually exist on disk. Without concrete proof of the created project structure, the task cannot be confirmed as completed.
- `T002a` (rejected 1x): No evidence of a Python virtual environment (e.g., a `venv/` directory with activation scripts, `pyvenv.cfg`, or installed packages) is present. The required artifact is missing, so the task of creating the venv has not been demonstrated.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, `black` settings) or documentation of their setup are present. The claim provides only unrelated project specifications, so the required linting/formatting tooling is not demonstrated.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

