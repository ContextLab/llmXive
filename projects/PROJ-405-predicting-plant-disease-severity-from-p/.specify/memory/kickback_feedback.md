# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `projects/PROJ-405/` directory (or any files within it) was provided; the implementer did not supply a directory listing, creation script, or any artifact confirming the required root directory structure exists.
- `T001b` (rejected 1x): No evidence was provided that the required subdirectories (`projects/PROJ-405/code/`, `data/`, `tests/`, `artifacts/`) actually exist or contain any files; the response only repeats the feature specification without showing the directory structure. The task’s core deliverable is missing.
- `T001c` (rejected 1x): No evidence of the required subdirectory tree under `projects/PROJ-405/specs/001-predict-plant-disease-severity/` is provided; the implementer did not supply any directory listing, screenshots, or files confirming that the subfolders exist. The task remains undone until the specified subdirectories are created and shown.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or CI scripts invoking ruff/flake8/black) were presented. Without these artifacts, we cannot confirm that the project has the required linting/formatting tools set up. The implementer must add the appropriate configuration files and demonstrate they are active.
- `T006a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006c` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No evidence of a `tests/` directory, pytest configuration files, or any unit/integration test code was provided; the required test framework setup is missing.
- `T016` (rejected 1x): The repository contains a `code/data_ingestion.py` file, but it is truncated and does not show a complete implementation that writes the merged dataset. Moreover, the required output file `data/processed/unified_analysis.csv` is absent from the project. Without a generated CSV containing the merged image features and weather data, the user story is not satisfied. The next implementer must finish the ingestion script (including feature extraction, weather linking, and CSV export) and ensure the `unified_analysis.csv` file is created and populated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

