# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or file system evidence were provided showing that the required folders (`code/data`, `code/models`, `code/eval`, `data/raw`, `data/processed`, `contracts`) actually exist; the response contains only the task description and specifications. The implementer must create and demonstrate the presence of these directories.
- `T001b` (rejected 1x): No evidence was provided showing that the `code/`, `data/`, and `tests/` directories exist or contain the required `__init__.py` and `.gitkeep` files; without these artifacts the initialization task cannot be confirmed as done.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `ruff.toml` or `.ruff.toml`, or CI scripts invoking ruff/black) are present, nor any documentation showing they have been set up. The required artifacts to prove that linting (ruff) and formatting (black) are configured are missing.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T012` (rejected 1x): The provided `download_gsm8k.py` is truncated (the `verify_solution_correctness` function ends mid‑line and no code to download, filter, or write the Parquet file is present), and the required `data/raw/gsm8k_verified.parquet` file does not exist. Consequently the task’s core requirements are not satisfied.
- `T015` (rejected 1x): The `data/processed/delta_coefficients.json` file exists but the required schema file `contracts/delta_oracle.schema.yaml` is missing, so conformance cannot be verified. Moreover, the JSON contains only a handful of token entries rather than the full set of coefficients for the 500‑example GSM8K subset required by the specification. The task is therefore not satisfied.
- `T018` (rejected 1x): The required output file `data/processed/static_features.parquet` does not exist, and the provided `extract_features.py` script is incomplete (truncated) with no visible logic that writes the required parquet with columns `[token_id, feature_vector]`. The task’s core deliverable is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

