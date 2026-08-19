# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing or evidence of the requested folders (`code/data`, `code/features`, `code/models`, `code/analysis`, `data`, `models`, `reports`, `tests/unit`, `tests/contract`, `tests/integration`) is provided, so we cannot verify that the project structure was actually created. The implementer must supply a concrete view of the filesystem showing these directories (and optionally placeholder files) to satisfy the task.
- `T003` (rejected 1x): The `pyproject.toml` correctly contains the `[tool.black]` section with the required settings, but the required `.ruff.toml` file is missing entirely; only a `[tool.ruff]` section is present inside `pyproject.toml`. The task explicitly demanded a separate `.ruff.toml` file with `line-length = 88` and `target-version = "py310"`. This artifact must be added to satisfy the requirement.
- `T004` (rejected 1x): No `data/`, `models/`, or `reports/` directories and no `.gitignore` file containing the required exclusion patterns are present in the provided artifacts. Consequently the required directory structure and ignore rules have not been demonstrated.
- `T006` (rejected 1x): The repository contains `code/utils/schema_validator.py` with a generic `load_schema` implementation, but the required schema files (`contracts/dataset.schema.yaml`, `contracts/model_output.schema.yaml`, `contracts/output.schema.yaml`) are absent (e.g., `schema.yaml` is missing) and the code snippet is truncated, so the function cannot be demonstrated to load the specified contracts schemas. The task therefore lacks the necessary schema artifacts.
- `T010` (rejected 1x): The test file `tests/contract/test_dataset_schema.py` exists, but the required schema file `contracts/dataset.schema.yaml` is missing, and there is no evidence that `data/clean_data.csv` is present. Without the schema (and the data file) the contract test cannot verify the dataset, so the task is not genuinely completed.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/integration/test_data_fallback.py
- `T012` (rejected 1x): The provided `code/data/download.py` contains only utility functions for synthetic data generation and does not implement any downloading from Zenodo or Materials Cloud, nor does it include exponential backoff or CSV output logic. Additionally, the required `data/raw_data.csv` file is absent. Both the core functionality and the expected output artifact are missing.
- `T014` (rejected 1x): The repository contains a `preprocess.py` file, but it is truncated and does not show the full `preprocess_data` implementation required to filter missing densities, check the row count, trigger synthetic data generation, and write `data/clean_data.csv` or `data/synthetic_data.csv`. Moreover, neither `data/clean_data.csv` nor `data/synthetic_data.csv` exists in the project. The task’s essential output artifacts and complete logic are therefore missing.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/clean_data.csv, data/validation_log.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

