# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`data/raw`, `data/processed`, `data/assets`) is provided; the artifact list is empty, so we cannot confirm that the directories were actually created.
- `T001b` (rejected 1x): No evidence was provided showing that the required directories (`code`, `artifacts`, `tests`) actually exist or contain any files; without such artifacts the task requirement is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `ruff.toml`, `pyproject.toml` with Black settings) or setup scripts are present in the provided evidence, so the requirement to configure flake8/ruff and Black has not been satisfied. The implementer must add the appropriate configuration files and any integration steps (e.g., pre‑commit hooks) to complete the task.
- `T009e` (rejected 1x): The required artifacts `data/raw/kinetic_dataset_raw.csv` and `data/raw/checksums.json` are both missing, so no checksum verification could be performed. The task’s core requirement is not satisfied.
- `T009f` (rejected 1x): The required artifact `data/assets/kinetic_dataset.csv` does not exist, so no data ingestion or schema validation has been performed. The implementer must create the CSV file with the verified data and ensure it conforms to the expected schema.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

