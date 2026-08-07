# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or file paths were provided showing that the required folders (`projects/PROJ-328-predicting-the-impact-of-composition-on-/data/`, `code/`, `tests/`, `models/`) actually exist; without concrete evidence the claim cannot be verified. The implementer must supply a directory tree or screenshots confirming the creation of these directories.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `setup.cfg`, `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) are present in the provided evidence, nor any CI steps showing they run after T001. Without these artifacts the requirement to configure flake8/black cannot be confirmed.
- `T005` (rejected 1x): No files or code were found under `code/ingestion/`, and there is no placeholder implementation for a literature aggregator. The required ingestion scaffolding artifact is missing, so the task is not satisfied.
- `T006` (rejected 1x): No evidence of a `code/features/` directory (or any files within it) was provided; the implementer did not supply the required directory structure or any placeholder indicating it has been created. Without the actual folder and its contents, the task requirement is not satisfied.
- `T007` (rejected 1x): No files or code snippets for `code/models/SolderComposition.py` or `code/models/CompositionalDescriptor.py` (or equivalent) were provided, so we cannot verify that the required data model classes exist, are non‑empty, and contain the appropriate fields. The implementer must add the two model definitions in the `code/models/` directory.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

