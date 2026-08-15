# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `setup.cfg`, `pyproject.toml` with Black settings) or related scripts were presented for the `code/` directory, and there is no evidence that flake8 and Black have been set up or integrated. The implementer must add the appropriate configuration files and ensure they are applied to the codebase.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): The provided `code/ingest.py` contains placeholder URL and checksum values, does not retrieve the DOI from the config, and the script is incomplete/truncated (missing the end of `main`). Moreover, the required output file `data/raw/bronze.parquet` is not present. The implementation therefore does not fulfill the download‑verify‑convert requirement.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/daily_aggregates.csv, schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

