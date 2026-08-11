# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure is shown or listed in the provided evidence; the implementer did not supply any proof that the required folders (`code/`, `data/raw/`, `data/processed/`, `data/models/`, `tests/unit/`, `tests/integration/`, `specs/`) actually exist. The task remains unfinished until those directories are created and demonstrated.
- `T001b` (rejected 1x): No `__init__.py` files were presented in the evidence; the implementer provided no directory listings or file contents showing empty `__init__.py` files in the new project directories. Without these artifacts, the requirement to create empty package initializers is not satisfied.
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` entries, `.ruff.toml`, `black.toml`, or a pre‑commit hook) were provided, nor any evidence that ruff and black have been set up in the repository. The required artifacts are missing.
- `T006` (rejected 1x): The implementer provided no evidence of a `tests/` directory (with unit and integration subfolders) in the repository; no files or structure were shown. Consequently the required artifact is missing, so the task is not satisfied.
- `T013` (rejected 1x): The repository contains a partially shown `code/data_ingestion.py` with a filtering function, but the script does not appear to finish writing the processed data, and the required output file `data/processed/heas_train.csv` is absent from the project. The task’s core deliverable – a CSV file of 5‑element‑or‑more systems – is therefore not present.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/holdout_known.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

