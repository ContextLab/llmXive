# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8` config) or scripts to install/run ruff/flake8 and black are present. The claim lacks any artifact demonstrating that linting and formatting have been set up.
- `T005` (rejected 1x): No `utils/config.py` file containing random seed settings and path constants was provided or referenced; the evidence contains only the task description and no actual code artifact. The required initialization script is missing.
- `T006` (rejected 1x): No `utils/provenance.py` file or its contents are present in the provided evidence, and thus the required `record_artifact(file_path, state_file)` function that computes a SHA‑256 hash and writes it to a state YAML file is missing. The task cannot be considered completed until this module is added with the specified functionality.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): No evidence was provided that a `data/` directory (with `raw/`, `processed/`, and `artifacts/` subfolders) actually exists in the project repository; the claim is unsupported by any listed files or screenshots. The required directory structure must be created and verified.
- `T011` (rejected 1x): The repository contains a `synthetic_generator.py` file, but it does not include code that writes the generated data to `data/raw/synthetic_bmg_seed.csv` nor does it show a call to `utils.provenance.record_artifact`. Moreover, the required CSV file is absent from the `data/raw` directory. The task’s core output and provenance step are therefore missing.
- `T016` (rejected 1x): The repository lacks the required fallback data file (`data/raw/synthetic_bmg_seed.csv`) and the schema file (`contracts/bmg_entry.schema.yaml`), both of which the ingest script must read and validate against. Without these artifacts the implemented `ingest.py` cannot fulfill the specified logic.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

