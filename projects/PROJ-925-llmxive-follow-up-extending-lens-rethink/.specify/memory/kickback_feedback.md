# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the requested directory hierarchy (`projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/` with the specified subfolders) is present; the implementer did not provide any file or folder listing to confirm the structure exists. The task therefore remains unfinished.
- `T001b` (rejected 1x): No directory listings or other evidence were provided to show that the required `data/raw`, `data/processed`, `code`, `code/tests`, `code/utils`, `code/models`, and `docs` folders actually exist at the project root. Without such artifacts, we cannot confirm the structure was created as specified.
- `T003` (rejected 1x): The implementer provided no linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with black settings, or pre‑commit hook definitions). Without these artifacts, the requirement to configure ruff/flake8 and black is not satisfied. The next implementer must add the appropriate configuration files and ensure they are functional.
- `T004a` (rejected 1x): No contracts were found in `specs/001-llmxive-follow-up-extending-lens-rethink/contracts/` (no dataset, feature_vector, deviation_target, or significance_results files), and the required `DataSchemaError` message is not present. The implementer provided only a textual description, not the actual schema files or error definition.
- `T004b` (rejected 1x): No `code/tests/contract/` directory or the expected test files (`test_dataset_schema.py`, `test_feature_vector_schema.py`) are present in the provided evidence, so the required scaffolding for contract validation tests has not been delivered.
- `T009` (rejected 1x): The required output file `data/raw/pick-a-pic.parquet` is not present, so the dataset has not been materialized as the task demands. Additionally, without the file we cannot verify that the script validates the `human_rating` column or raises the exact `DataSchemaError` message on failure. The missing parquet file must be generated for the task to be considered complete.
- `T015b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/logs/exclusions.log, data/processed/exclusion_summary.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

