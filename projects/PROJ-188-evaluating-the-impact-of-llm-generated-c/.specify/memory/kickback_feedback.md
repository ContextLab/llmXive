# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): No artifact was provided showing that the Constitution has been amended to align Principle VII with Spec FR‑001, nor any script or log confirming the check and error handling. The required verification and amendment evidence are missing.
- `T001a` (rejected 1x): No evidence of the required `projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/` directory or any of its contents (scripts, data files, etc.) is provided, so the task’s primary deliverable cannot be confirmed. The implementer must create the project folder at the repository root and include the necessary curation, generation, and validation scripts/data.
- `T001b` (rejected 1x): No evidence of the required `code/` and `tests/` subdirectories was provided; the artifact list is empty, so we cannot confirm that the directories were created. The implementer must add the two directories (with at least placeholder files) to satisfy the task.
- `T001c` (rejected 1x): No evidence of a `data/` folder with the required `raw/`, `intermediate/`, and `processed/` subdirectories is provided; without visible artifacts, we cannot confirm the directories were created. The implementer must add these directories (or show a directory listing) to satisfy the task.
- `T001d` (rejected 1x): No evidence was presented showing that empty `__init__.py` files exist in the `code/` and `tests/` directories; without those files the task requirement is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) are present, nor any documentation showing that ruff and black have been set up for the project. The provided artifacts relate only to dataset generation and study design, not to the required linting/formatting configuration.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

