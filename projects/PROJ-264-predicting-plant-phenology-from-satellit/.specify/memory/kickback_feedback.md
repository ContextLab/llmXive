# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): No code, data files, model artifacts, or performance reports were provided; the claim references an unspecified placeholder and there is no concrete evidence that the ingestion pipeline, model training, or sensitivity analysis were implemented or executed. The required deliverables are missing.
- `T003` (rejected 1x): The claim provides no visible configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or a `black` config) or any script/command showing that ruff linting and black formatting have been set up for the project. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied. The next implementer should add the appropriate configuration files and ensure they are non‑empty and correctly reference ruff and black.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: src/config.py
- `T006` (rejected 1x): No `tests/contract/` directory, pytest‑jsonschema configuration, or validation scripts are present, and there is no generated artifact linking `config.py` to `contracts/config_schema.json` or updating `data-model.md`. Consequently the required testing framework and documentation output are missing.
- `T008` (rejected 1x): No directory hierarchy under `data/raw/` or `data/processed/` and no checksum scripts are provided in the evidence; the implementer did not supply any files or code to demonstrate the required structure or functionality.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

