# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`code/`, `tests/`, `data/raw/`, `data/processed/`, `code/models/`, `code/analysis/`) is provided; without a listing or screenshots we cannot confirm they exist. The implementer must supply proof that the specified folder hierarchy has been created.
- `T001b` (rejected 1x): No evidence of `__init__.py` files in the `code/` subdirectories or in `tests/` was presented; without a file listing or the actual files, we cannot confirm they exist. The implementer must add and show the created `__init__.py` files in every required directory.
- `T001c` (rejected 1x): The claim provides no evidence that `.gitkeep` files exist in `data/raw/` or `data/processed/`; without the actual files present, the requirement of creating them to track the directories is not satisfied. The next implementer must add a `.gitkeep` (or any placeholder file) in each of those two directories.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or a `pre-commit` hook) are present, nor any documentation showing that `ruff` and `black` have been set up for the project. The claim provides only unrelated feature specifications, so the required linting/formatting setup is missing.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No configuration files, scripts, or documentation were presented that define or manage environment variables for data paths. The claim provides no tangible artifact (e.g., a `.env` file, a Python module using `os.getenv`, or instructions) to verify that environment variable management has been set up. Consequently, the requirement is not satisfied.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/reconstruction_1610_2002.parquet
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/variance_analysis.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

