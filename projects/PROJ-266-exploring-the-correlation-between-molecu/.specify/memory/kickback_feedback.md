# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `code/`, `tests/`, and `data/` directories was provided; the claim lacks any actual artifact showing the project structure exists. The implementer must create and show these folders (with at least placeholder files) to satisfy the task.
- `T003` (rejected 1x): No linting configuration files (e.g., .flake8, pyproject.toml/black settings, or pre‑commit hooks) are present in the provided evidence, so the task of configuring flake8/black and formatting tools is not satisfied. The implementer must add the appropriate configuration artifacts and ensure they are functional.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): The submission provides only the task description and feature specification; there is no evidence of the required `data/raw/` and `data/processed/` directories being created, nor any script or utility for generating checksums. Without these artifacts, the task’s core requirement is not satisfied.
- `T012` (rejected 1x): The `tests/contract/test_dataset.py` file exists, but the required `dataset.schema.yaml` file is missing, so the contract tests cannot actually validate the dataset against a schema. The missing schema file must be added (with the expected columns, types, etc.) for the task to be complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

