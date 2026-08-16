# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/`, `code/`, `data/`, `tests/`) is provided; the implementer did not supply any artifact confirming the directory structure exists. The task remains unfinished until these folders are created and shown.
- `T001b` (rejected 1x): No evidence was provided showing that `__init__.py` files actually exist in the `code/` and `tests/` directories; without those files present, the task requirement is not satisfied. The implementer must add non‑empty `__init__.py` files to both directories.
- `T001c` (rejected 1x): No evidence of `.gitkeep` files in `data/raw/`, `data/interim/`, or `data/processed/` was provided; the artifact list is empty, so the requirement of creating those placeholder files is not satisfied. The next implementer must add a `.gitkeep` (or equivalent empty placeholder) file to each of the three directories.
- `T003` (rejected 1x): No linting/formatting configuration files (e.g., pyproject.toml, .ruff.toml, black settings, or pre‑commit hooks) are provided or referenced, so there is no evidence that ruff and black have been configured for the project. The required artifacts are missing.
- `T008` (rejected 1x): No evidence of a `tests/` directory or its `unit`, `integration`, and `contract` subfolders was provided; the implementer did not supply any files or directory listings showing the required structure. The task therefore remains unfinished.
- `T015` (rejected 1x): The repository contains a `code/main.py` with a `generate_ingestion_summary` function, but the script never runs it (no orchestration entry point) and the required output file `data/processed/ingestion_summary.json` is absent from the project. Consequently the task of actually generating the ingestion summary JSON with peak counts is not fulfilled.
- `T033` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/summary_table.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

