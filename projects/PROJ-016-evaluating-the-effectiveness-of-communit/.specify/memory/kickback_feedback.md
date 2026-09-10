# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/data`, `code/analysis`, `code/tests`, `data/raw`, `data/processed`, `docs/output`) is provided; the claim lacks any artifact or directory listing to confirm they were created. The task cannot be considered complete until the specified folder structure exists and is visible.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present in the provided evidence, so the requirement to configure ruff/flake8 and black cannot be verified as fulfilled. The implementer must add the appropriate configuration artifacts and ensure they are non‑empty.
- `T004` (rejected 1x): No evidence was provided showing that the required directories (`data/raw/`, `data/processed/`, `docs/output/`) actually exist in the repository; the claim is unsubstantiated. The implementer must add the directory structure (or a manifest confirming its creation) to satisfy the task.
- `T007` (rejected 1x): The `code/tests/__init__.py` file exists, but the required `conftest.py` file is missing entirely, so the pytest framework setup is not fully provided. The task demands both files; without `conftest.py` the setup is incomplete.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/total_records_count.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

