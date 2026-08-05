# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or other evidence were provided showing that the required folders (`code/`, `data/raw/`, `data/derived/`, `data/processed/`, `tests/`, `state/`) actually exist in the repository. The implementer’s claim cannot be verified without concrete artifacts.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with black settings) or related setup scripts were provided, so the requirement to configure ruff/flake8 and black is not demonstrated. The implementer must add the appropriate config files and ensure they are non‑empty and correctly set up.
- `T004` (rejected 1x): No evidence was presented that the required directories (`data/raw/`, `data/derived/`, `data/processed/`) actually exist in the repository; the claim is unsupported and the artifact is missing.
- `T007` (rejected 1x): No `code/models/` directory or model files (`Participant`, `Stimulus`, `GazeEvent`) are present in the provided evidence; thus the required data model classes are missing. The implementer must add the three model definitions with the specified fields in the correct location.
- `T008` (rejected 1x): No logging configuration files, code changes, or documentation were provided to demonstrate that a logging infrastructure capturing data‑quality warnings and exclusion counts has been set up. The artifact required by task T008 is missing, so the requirement is not satisfied.
- `T004b` (rejected 1x): The repository lacks the required input file `data/raw/eye_tracking_raw.parquet` and the output file `data/derived/empirical_outcomes.csv`. Moreover, the provided `code/01_extract_empirical_outcome.py` is truncated and does not show the full logic for extracting columns, handling alias mapping, or writing the CSV, so the implementation cannot be verified as complete. The missing data file and incomplete script must be provided/fixed.
- `T017` (rejected 1x): No code, script, documentation, or test output was provided that demonstrates the preprocessing pipeline now treats zero fixations on the source ROI as valid data with a duration of 0 instead of marking it missing. Without an artifact showing this logic change (e.g., updated function, unit test, or log example), the requirement is not satisfied. The implementer must supply the modified implementation and evidence (e.g., a test case confirming a trial with zero source fixations yields duration 0).

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

