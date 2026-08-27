# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No project files or directory tree were presented; there is no evidence of a created codebase, folder hierarchy, or any non‑empty artifact that would constitute the required project structure. The implementer must add the actual project scaffold (e.g., README, src/, data/, scripts/, config files) to satisfy the task.
- `T003` (rejected 1x): The implementer provided only a feature specification for uncertainty quantification and no linting/formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml`, or a pre‑commit hook). Consequently, the required artifact to configure Ruff and Black is missing.
- `T005` (rejected 1x): The repository contains a `code/data/download.py` that defines a download function, but the required output file `data/raw/oqmd.parquet` does not exist. The task demands that the dataset be actually saved to that path, which is missing. The implementer must run the script (or otherwise provide the parquet file) so the raw data is present.
- `T006` (rejected 1x): The provided `preprocess.py` defines loading, missing‑value exclusion, and a stub for stratified splitting, but it never performs PCA to 20 components, never writes `features_20pca.csv` or `exclusion_log.json`, and does not tie the config values (`split_type`, `seed`) into the processing flow. These required steps are missing, so the implementation does not satisfy the task.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/validation_report.json, data/processed/exclusion_log.json, data/validation_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

