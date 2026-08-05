# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001b` (rejected 1x): No evidence was provided that a `data/` directory with the required `raw`, `interim`, and `processed` subfolders actually exists; the artifact list is empty, so the implementer has not demonstrated that the directories were created.
- `T001c` (rejected 1x): No evidence was provided that a `code/` directory containing an `__init__.py` file and a `tests/` subdirectory actually exists; the submission includes only specification text and no filesystem artifacts.
- `T001d` (rejected 1x): No evidence of the required `tests/unit/` or `tests/integration/` directories was provided; the implementer did not include any file listings, screenshots, or code showing these folders exist. The task therefore remains unfinished.
- `T001e` (rejected 1x): No evidence of a `reports/` directory (or any files within it) was provided; the implementer’s claim is unsupported by any visible artifact. The required directory must be created and contain the final output files for the task to be considered complete.
- `T003` (rejected 1x): No linting/formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or a pre‑commit config) are present in the repository, nor any documentation showing that Ruff and Black have been set up and integrated. Without these artifacts the requirement to configure the tools is not satisfied.
- `T005` (rejected 1x): No script, code file, or documentation for a system‑level dependency check of FSL/AFNI is present; the only provided material is the project specification, which does not include the required artifact. The task remains undone.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/preprocessing_stats.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

