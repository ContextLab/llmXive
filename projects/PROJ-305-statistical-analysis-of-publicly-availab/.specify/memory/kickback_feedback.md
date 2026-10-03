# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (`src/`, `tests/`, `data/`, `output/`) is provided; the claim lacks any artifact showing that these folders exist or contain files. The implementer must create and show the directory structure to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or related scripts) were found in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): The provided `src/data/validate.py` is truncated (the `validate_data` function ends mid‑line) and cannot fully perform validation, and the required `dataset.schema.yaml` file is missing, so the script cannot actually check raw data against a schema as the task demands. The implementation must be completed and the schema file supplied.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/plots.py
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/clean.py
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/clean.py
- `T027` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/sensitivity.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

