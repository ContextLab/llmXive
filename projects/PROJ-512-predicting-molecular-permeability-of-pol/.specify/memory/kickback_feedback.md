# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): The `pyproject.toml` file is present, but the required `.ruff.toml` file does not exist, so the deliverable of providing both configuration files is not satisfied. The missing `.ruff.toml` must be added with explicit Ruff settings.
- `T010` (rejected 1x): The `ingestion.py` script does not save raw data checksums to `raw/checksums.json` (the file is missing) and the `main` function is truncated, leaving no real NIST/PubChem URL or logic to download actual data. Moreover, only the “< 500 records” case raises the required `DataUnavailableError` message; other failure modes (e.g., 404) raise a different message. The task’s core requirements are therefore not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

