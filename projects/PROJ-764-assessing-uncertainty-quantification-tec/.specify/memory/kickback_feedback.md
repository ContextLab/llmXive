# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure (`code/`, `data/`, `results/`, `tests/`, `docs/`) is presented or referenced in the provided evidence; without visible artifacts, the requirement cannot be confirmed as satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or a pre‑commit hook setup) are present in the provided evidence, so the requirement to configure Ruff and Black is not demonstrated. The implementer must add the actual configuration artifacts and ensure they are non‑empty.
- `T005` (rejected 1x): The repository contains `code/data/download.py`, but the required output files `data/raw/oqmd.parquet` and `data/checksums.json` are absent, so the dataset was not materialized nor its checksum recorded as the task demands.
- `T006a` (rejected 1x): The provided `preprocess.py` defines helper functions for loading config, loading data, binning, and a stratified split, but the script does not contain code that actually reads the config, performs the split, and writes `data/processed/raw_train.csv`, `raw_val.csv`, and `raw_test.csv`. Moreover, those three CSV files are absent from the repository. The task’s core output—generating the split CSV files—is therefore not fulfilled.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/validation_report.json, data/processed/exclusion_log.json, data/validation_report.json
- `T015` (rejected 1x): The repository contains `code/models/sparse_gp.py`, but the file is truncated and does not include a full training routine or model saving logic. Moreover, the required input files `data/processed/features_test_20pca.csv` and `data/processed/pca_transformer.pkl` are absent, and the expected output artifact `results/models/sparse_gp_model.pt` was not produced. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

