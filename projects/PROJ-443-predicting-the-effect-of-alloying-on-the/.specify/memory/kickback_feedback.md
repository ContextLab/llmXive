# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The provided evidence only describes user stories and testing criteria; there is no indication that the required directories (`src/`, `tests/`, `data/raw/`, `data/processed/`, `results/`) actually exist or contain any files. The task’s core deliverable—a project folder structure—is missing.
- `T003` (rejected 1x): No project files (e.g., `pyproject.toml`, `requirements.txt`, `setup.cfg`, or a virtual environment) are provided, nor any evidence that a Python 3.11 project with the listed dependencies has been created. The only artifact is a textual feature specification, which does not satisfy the task of initializing the project with the required packages. The implementer must supply the actual project scaffold and dependency declarations.
- `T004` (rejected 1x): The provided evidence contains only a feature specification for data ingestion and modeling; there are no linting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) or any mention of setting up flake8/black. Consequently, the requirement to configure linting and formatting tools is not satisfied.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/data_fetch.py
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/validators.py
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logging_config.py
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: src/models/hea_sample.py
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/fetch_oqmd.py, data/source_metadata.yaml
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/fetch_mp.py
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/filter.py
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/normalize.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

