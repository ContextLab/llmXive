# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings, screenshots, or other evidence were provided to show that the required folders (`code/data`, `code/models`, `code/utils`, `code/config`, `data/raw`, `data/processed`, `state`, `output`, `tests/contract`, `tests/integration`, `tests/unit`, `docs/paper`, `docs/reports`) actually exist in the project. Without concrete proof of the created structure, the task cannot be considered completed.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, `black` settings) or related scripts were presented. The claim provides no artifact demonstrating that ruff/flake8 and black have been set up, so the requirement is not satisfied.
- `T004a` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories was provided; the artifact list is empty, so the filesystem structure cannot be confirmed as created. The implementer must add the actual directories (or a screenshot/listing) to satisfy the task.
- `T014` (rejected 1x): The repository contains a `code/data/features.py` file, but it is truncated and does not show the full implementation nor any code that writes `data/processed/features.csv`. Moreover, the required output file `data/processed/features.csv` is absent from the project. Without the generated CSV matching the schema, the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

