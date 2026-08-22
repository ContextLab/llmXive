# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings, creation scripts, or verification output were provided to show that `code/01_ingest/`, `code/02_process/`, `code/03_model/`, `code/04_validate/`, and `code/05_viz/` actually exist, so the required artifact is missing.
- `T001b` (rejected 1x): No directory listings or file system evidence were provided showing that `utils/`, `tests/`, `data/raw/`, `data/processed/`, and `data/models/` actually exist and contain any content. Without such artifacts, we cannot confirm the task was completed.
- `T001c` (rejected 1x): No evidence of the `tests/contract/` or `tests/unit/` directories or their `.gitkeep` files is provided; without seeing those paths and files, we cannot confirm the required artifacts exist.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with black settings) or setup scripts are present in the provided evidence. Consequently, the requirement to configure ruff/flake8 and black is not satisfied.
- `T007` (rejected 1x): No evidence of the `data/raw/` and `data/processed/` directories or the required `.gitkeep` placeholder files is present; the artifact list is empty, so the task’s requirement is not satisfied.
- `T008` (rejected 1x): No `tests/contract/` directory or any schema‑validation helper files are present in the repository; the claim lacks any concrete artifacts to verify that the required stubs were created. The task therefore remains unfinished.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: code/02_process/run_snippy.sh

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

