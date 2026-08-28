# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` directory (or any files within it) is provided; the only artifacts shown are feature specifications, not the actual project root folder. The task’s core requirement—creating the project root directory—is therefore unmet.
- `T002` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `data/reports/`) inside `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` is presented; the artifact list is empty, so the task is not satisfied.
- `T003` (rejected 1x): No evidence of the required directories (`code/data/`, `code/tests/`, `code/utils/`) inside `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` is provided; the artifact list is empty, so the task is not satisfied.
- `T004` (rejected 1x): No evidence of a Python virtual environment (e.g., a `venv` or `.venv` directory with activation scripts and installed packages) exists in the specified path, and no related artifact was supplied. The required environment was not created.
- `T006` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a `pre-commit` hook) were presented for the `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` directory, so the required artifact does not exist. The task remains undone.
- `T008` (rejected 1x): The `validation.py` module is present, but the required schema files (`contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`) are missing, so the utilities cannot actually validate against them. Additionally, the provided code is truncated and does not show concrete functions that load and apply those specific schemas. The missing schema files must be added (or created) and the validation utilities should be demonstrated to use them.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

