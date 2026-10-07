# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or setup scripts are present in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied. The implementer must add the appropriate configuration files and ensure they are integrated into the project.
- `T004` (rejected 1x): No evidence was provided showing that the required directories (`data/raw/`, `data/processed/`, `state/projects/`) actually exist or contain any files; the claim is unsubstantiated. The implementer must create and demonstrate the presence of these directories (and optionally include placeholder files) to satisfy the task.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): The provided evidence only describes election poll aggregation features and contains no code, script, or files that compute SHA‑256 hashes or modify `state/projects/PROJ-206-*.yaml`. The required state‑management utility and its YAML updates are entirely missing.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/main.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

