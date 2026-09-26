# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure (`src/`, `tests/`, `data/raw`, `data/processed`, `data/results`) is shown or referenced in the provided artifacts; the implementer only supplied a feature specification without any file system evidence. The required folders are missing.
- `T002` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or a pre‑commit hook) were supplied, nor any evidence that the tools have been installed or integrated into the project. The required artifacts to demonstrate that ruff and black are configured are missing.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/config.py
- `T006` (rejected 1x): No pytest configuration file (e.g., `pytest.ini` or `pyproject.toml` with pytest settings) or test directory (e.g., `tests/` with placeholder test modules) was provided. Without these artifacts the requirement to set up pytest and its test structure is not satisfied.
- `T010` (rejected 1x): The required `data/processed/filtered_cohort.csv` file does not exist, and the referenced schema file `contracts/dataset.schema.yaml` (or `schema.yaml`) is also missing, so the contract test cannot actually validate anything. The test script is present but without the data and schema it cannot be executed, meaning the task’s core requirement is unmet.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/synthetic_gen.py
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/ingestion.py
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/filtering.py
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/filtering.py
- `T015` (rejected 1x): The required file `src/data/filtering.py` does not exist, so no logic, imputation handling, or logging has been implemented. The task’s core artifact is missing entirely.
- `T016` (rejected 1x): The required artifact `tests/unit/test_diversity.py` does not exist on disk, so no unit tests for Shannon, Simpson, or Chao1 calculations are present. The task cannot be considered fulfilled until this file is created with appropriate test cases.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

