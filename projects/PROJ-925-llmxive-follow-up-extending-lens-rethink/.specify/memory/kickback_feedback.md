# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the requested directory hierarchy (`projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/` with the specified subfolders) is present; the implementer did not provide any file or folder listing to confirm the structure exists. The required artifact is missing.
- `T001b` (rejected 1x): I could find no evidence that the required directories (`data/raw`, `data/processed`, `code`, `code/tests`, `code/utils`, `code/models`, `docs`) actually exist in the repository; no file‑tree or screenshots were provided. The task’s deliverable is the creation of this folder structure, and without concrete proof of those directories being present, the requirement is not satisfied.
- `T003` (rejected 1x): The repository provides no visible linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or CI scripts invoking these tools). Without such artifacts, the requirement to configure ruff/flake8 and Black is not satisfied. The next implementer should add the appropriate configuration files and ensure they are integrated into the development workflow.
- `T004` (rejected 1x): No contracts were found under `specs/001-llmxive-follow-up-extending-lens-rethink/contracts/`, and there is no definition of a `DataSchemaError` with the required message. The implementer did not provide the required schema files (dataset, feature_vector, deviation_target, significance_results) nor the error message implementation.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

