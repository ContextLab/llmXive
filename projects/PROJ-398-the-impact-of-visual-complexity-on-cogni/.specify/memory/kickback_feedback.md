# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure (`src/lib/`, `src/metrics/`, `src/experiment/`, `src/analysis/`, `tests/`) is shown in the provided evidence; without visible folders or files, we cannot confirm the required code layout exists. The implementer must supply the actual directory tree (or a screenshot/listing) demonstrating these folders are present and contain at least placeholder files.
- `T001b` (rejected 1x): No directory listings or file system evidence were provided showing that `data/stimuli/`, `data/processed/`, `data/measurements/`, and `data/raw/` actually exist; the response contains only the task description and specifications, not the required artifacts.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or pre‑commit hooks) are present in the provided evidence, nor any documentation showing that ruff and black have been set up and integrated into the project. Without these artifacts, the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: src/lib/utils.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

