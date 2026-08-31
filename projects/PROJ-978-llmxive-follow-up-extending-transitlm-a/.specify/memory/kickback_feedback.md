# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory tree (`code/`, `data/raw/`, `data/processed/`, `data/analysis/`, `models/`, `analysis/`, `tests/`, `docs/`) is provided; the artifacts are missing, so the task is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` or `.ruff.toml` for ruff, and black settings or a pre‑commit hook) are present in the provided artifacts, and the evidence only describes a research feature spec unrelated to configuring ruff/black. The required linting/formatting setup is missing.
- `T004` (rejected 1x): The `data/download.py` script exists but is incomplete (truncated) and does not demonstrably perform a streaming download, SHA256 verification, or write the required `data/raw/transitlm_ground_truth.json` file, which is missing from the repository. The essential output artifact is absent, so the task is not fulfilled.
- `T006a` (rejected 1x): The required `data/preprocess.py` file (which should contain the `filter_cities` implementation) is missing, and the produced `city_filtered_routes.jsonl` only includes routes for three cities and is truncated, so the four‑city filter is not correctly realized.
- `T006b` (rejected 1x): The required source file `data/preprocess.py` (which should contain the `apply_vocabulary_restriction` function) is missing, so the implementation cannot be verified. While a `vocab_restricted_routes.jsonl` file is present, without the function definition the task’s core requirement is not satisfied. The missing script must be added and the function correctly implemented.
- `T006c` (rejected 1x): The required `data/preprocess.py` file does not exist, so the `stratify_routes` function cannot be verified or executed. The provided `stratified_routes.parquet` is only a placeholder description, not an actual populated Parquet file, and no evidence shows that it contains rows or balanced categories. The core deliverable and its verification are therefore missing.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/preprocess.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

