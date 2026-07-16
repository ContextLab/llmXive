# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No project structure (e.g., directory layout, placeholder files, README, or configuration) was provided; the evidence contains only the specification text and no actual artifacts demonstrating that a repository or folder hierarchy was created. The required artifact is missing.
- `T002` (rejected 1x): The only evidence is a high‑level feature specification; there is no project directory, no Python 3.11 setup, and no file (e.g., `requirements.txt`, `pyproject.toml`, or `environment.yml`) listing the required packages with pinned versions. Consequently the core deliverable—an initialized Python project with the specified pinned dependencies—is missing.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or equivalent) are present in the provided evidence, so the requirement to configure flake8/black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty.
- `T004` (rejected 1x): No evidence of the required directories (`data/raw`, `data/processed`, `data/splits`, `results`) being created or listed is provided; the claim lacks any artifact confirming the directory structure exists.
- `T007` (rejected 1x): The required schema file `contracts/dataset.schema.yaml` is missing, and the `src/utils/validate_schema.py` implementation is incomplete (truncated and contains a broken line `raise InsufficientD`). Both artifacts are needed to satisfy the task.
- `T008` (rejected 1x): No code, configuration files, or documentation defining custom exception classes or error‑handling logic for data‑ingestion failures were provided. Consequently the required artifact (error‑handling implementation) is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

