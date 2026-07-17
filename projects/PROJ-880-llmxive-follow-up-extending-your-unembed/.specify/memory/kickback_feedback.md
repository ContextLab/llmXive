# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/raw/`, `data/processed/`, `tests/`, `contracts/`) is provided; without visible artifacts we cannot confirm the project structure was created.
- `T003` (rejected 1x): The implementer supplied only a feature specification for edge‑spectrum experiments and no files, scripts, or configuration (e.g., `pyproject.toml`, `.flake8`, `black` config, CI setup) that set up flake8/black linting and formatting. Consequently the required linting configuration artifact is missing.
- `T009` (rejected 1x): The repository lacks the required `similarity_report.schema.yaml` file, so the test cannot load or validate against the intended schema. Additionally, the provided `tests/contract/test_schemas.py` snippet shows only helper functions and no concrete test case exercising the similarity report schema. Both the schema file and a concrete test are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

