# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listing or file tree was provided showing the required folders (`src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `output/`, `contracts/`, `logs/`). Without concrete evidence that these directories exist and are non‑empty, the claim that the project structure is created cannot be verified. The implementer must supply a file system snapshot (e.g., `tree` output or a zip archive) demonstrating the presence of all required directories.
- `T001b` (rejected 1x): No `.gitignore` or `README.md` files were presented in the evidence, nor any content showing they contain a project title and description. The required stub files are missing, so the task is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present in the provided evidence, nor any documentation showing that ruff/flake8 and black have been set up for the project. Consequently, the requirement to configure these tools is not satisfied.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): The `src/data/validate.py` file is truncated (ends abruptly in `sys.exit(E_SCH`) and does not contain a complete validation routine that checks the data against a schema and exits with `E_SCHEMA_MISSING` on failure. Moreover, the required `contracts/dataset.schema.yaml` (or `schema.yaml`) is absent from the repository, so the validator cannot even load the schema. Both the implementation and the necessary schema file are missing.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/plots.py
- `T016b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/download_meddra.py, data/meddra_soc_mapping.csv
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/clean.py
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/clean.py
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/clean.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

