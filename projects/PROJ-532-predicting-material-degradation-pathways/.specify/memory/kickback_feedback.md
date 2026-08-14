# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory `projects/PROJ-532-predicting-material-degradation-pathways/` (or any of its sub‑folders/files) is presented, so we cannot confirm that the project structure was actually created. The implementer must provide the directory listing or the actual files that constitute the project scaffold.
- `T003` (rejected 1x): No configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) or any other evidence of linting/formatting setup in the `code/` directory were presented. Without such artifacts, the claim that linting and formatting tools are configured cannot be verified.
- `T006` (rejected 1x): No evidence of a `results/` directory or its subfolders (`metrics/`, `plots/`, `artifacts/`) was provided; the implementer did not supply any artifact confirming the required directory structure exists.
- `T018` (rejected 1x): The required output file `data/processed/cleaned_alloys.csv` does not exist, so the ingestion step has not produced the cleaned dataset. While `retention_audit.json` is present and contains the expected statistics, the primary artifact the task mandates is missing. The next implementer must ensure `ingestion.py` actually creates `cleaned_alloys.csv` (with ≥200 records and ≥70% retention) and logs the stats.
- `T019` (rejected 1x): The provided `code/preprocessing.py` is truncated and contains syntax errors (e.g., an unfinished line `fe_pct = get_pc`). Moreover, the required output files `data/processed/train_set.parquet` and `data/processed/test_ood_set.parquet` are missing, and there is no evidence of a generated OOD split report. The task’s core functionality and artifacts are therefore not present.
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/integration/test_model_pipeline.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

