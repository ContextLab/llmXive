# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or screenshots were provided showing that the required folders (`code/ingestion`, `code/features`, `code/modeling`, `code/utils`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`, `docs`) actually exist in the repository. Without concrete evidence of these paths being created, the task requirement is not satisfied.
- `T003` (rejected 1x): The `code/.ruff.toml` file exists and contains the correct linting and formatting rules, but there is no evidence that the `ruff` package was actually installed (e.g., no entry in `requirements.txt`, `pyproject.toml`, or installation script). The task’s “Install `ruff`” requirement is therefore unmet.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T012` (rejected 1x): The integration test file exists but is truncated and never actually creates or validates a real DataFrame against the schema. Moreover, the required schema file `contracts/mg_dataset.schema.yaml` is missing, causing the test’s fixture to fail. Both the test implementation and the schema artifact need to be completed.
- `T013` (rejected 1x): No `fetch_data.py` file is present in `code/ingestion/`, and therefore there is no implementation that queries the Materials Project and AFLOWlib APIs or collects the required entries. The required artifact is missing.
- `T016` (rejected 1x): No `descriptors.py` file (or its contents) is present in `code/features/`, and no code implementing the weighted mean atomic radius, electronegativity variance, VEC, or atomic size mismatch calculations is provided. The required artifact is missing, so the task is not satisfied.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/clean_mg_data.parquet

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

