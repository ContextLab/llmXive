# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or file system evidence were provided, so we cannot verify that the required folders (`code/`, `code/data/`, `code/analysis/`, `code/audit/`, `code/utils/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `reports/figures/`) actually exist. The implementer must supply a concrete view (e.g., a tree dump or screenshots) showing these directories created and non‑empty.
- `T001b` (rejected 1x): No `__init__.py` files are presented in the provided evidence, and there is no directory listing or file content showing that they exist in every `code/` subdirectory. Without these files, the required Python package structure has not been demonstrated. The implementer must add the missing `__init__.py` files (and show their presence) for all relevant subfolders under `code/`.
- `T003` (rejected 1x): No configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) or CI scripts were provided to demonstrate that `ruff` linting and `black` formatting have been set up. The evidence lacks any artifact showing the tools are installed, configured, or integrated, so the task is not satisfied.
- `T033` (rejected 1x): The repository contains the required `code/analysis/save_complexity_scores.py` script, but the expected output file `data/processed/complexity_scores.csv` is absent. Without this CSV (with `pr_id` and `complexity_score` columns), the task’s core requirement is not met. The next implementer must run the script (or ensure it writes the file) so that the CSV is created in the specified location.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

