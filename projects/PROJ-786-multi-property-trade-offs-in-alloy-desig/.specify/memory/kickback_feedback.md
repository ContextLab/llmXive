# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or any command‑line instructions are present in the provided evidence, so the requirement to configure ruff and black is not satisfied. The implementer must add the appropriate configuration files and demonstrate that they are functional.
- `T004` (rejected 1x): No evidence of a `data/raw` or `data/processed` directory (with non‑empty `.gitkeep` files) was provided; the claim cannot be verified against any actual artifacts. The required directory structure and placeholder files are missing.
- `T008` (rejected 1x): No code, configuration files, or documentation for error handling or structured logging were provided; the claim cannot be verified against any tangible artifact. The required logging infrastructure is missing.
- `T015` (rejected 1x): The repository contains a `code/main.py` file, but it is truncated and does not show a complete orchestration that calls both ingestion and encoding and writes `data/processed/encoded_alloys.csv`. Moreover, the expected output file `data/processed/encoded_alloys.csv` is absent from the project. The required artifact is missing, so the task is not satisfied.
- `T016` (rejected 1x): No code, tests, or documentation were provided that adds validation to ensure feature vectors contain at least two periodic descriptors per element. The required artifact (e.g., a function/module with the validation logic and corresponding unit tests) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

