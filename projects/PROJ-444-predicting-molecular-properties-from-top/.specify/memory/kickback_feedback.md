# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No project directory `projects/PROJ-444-predicting-molecular-properties-from-top/` or any files within it are present in the provided evidence, so the required project structure has not been demonstrated. The task remains undone.
- `T003` (rejected 1x): No linting or formatting configuration artifacts (e.g., ruff settings, black config, or pyproject.toml entries) are present; therefore the requirement to configure ruff and black is not satisfied.
- `T004` (rejected 1x): No `data/` directory with the required `raw/` and `processed/` subfolders, nor any `state/` tracking artifacts are present in the provided evidence. The implementer did not supply the filesystem structure or files that would demonstrate the task was completed.
- `T007` (rejected 1x): The `code/00_checksum_verify.py` script is incomplete (the `main` function is truncated and never calls `write_checksums` to generate the checksum file), and the required output file `data/checksums.txt` is missing from the repository. The task’s core requirement—to compute SHA256 hashes of raw data and record them in `data/checksums.txt`—has not been fulfilled.
- `T010` (rejected 1x): The `tests/contract/test_tda_schema.py` file is present but ends abruptly with an incomplete `test_feature_vector_length` function (truncated line and missing closing parentheses), making the test syntactically invalid. Consequently, the contract test does not fully implement the required schema checks. The missing or broken test code must be completed for the task to be considered done.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

