# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): The provided evidence only contains a feature specification for fMRI entropy analysis and does not include any linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black settings) or instructions showing that ruff and black have been set up. Consequently, the requirement to configure linting (ruff) and formatting (black) tools is not satisfied.
- `T005` (rejected 1x): The repository contains `code/data_loader.py`, but the provided excerpt ends before any subject‑filtering, exclusion‑logging, or CSV‑writing logic, and the required output files are absent: `data/raw/checksums.sha256` and `data/raw/exclusions.log` do not exist, and `data/derived/valid_subjects.csv` only contains placeholder comments with no actual subject entries. The task’s core outputs are therefore missing.
- `T007` (rejected 1x): No code or data defining the required classes (`Subject`, `Parcel`, `EntropyFeature`) was provided; there is no artifact on disk showing these base data structures, so the task’s deliverable is missing.
- `T008` (rejected 1x): No environment configuration files, scripts, or documentation (e.g., conda `environment.yml`, Dockerfile, or README instructions) were provided to demonstrate that the project has been set up for CPU‑only execution without CUDA flags. Consequently, the required artifact is missing.
- `T012` (rejected 1x): The required integration test file `tests/integration/test_us1_pipeline.py` does not exist in the repository, so the task’s deliverable is missing. The implementer must add the test file implementing the full US1 pipeline on 2 subjects.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

