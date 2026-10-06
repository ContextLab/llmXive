# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory hierarchy (`code/`, `code/data/`, `code/geometry/`, `code/analysis/`, `code/tests/`, `code/tests/unit/`, `code/tests/integration/`, `data/raw/`, `data/processed/`) is provided; the implementer has not supplied any artifact confirming that these folders were created. The task remains undone.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or related scripts) were provided or referenced, so we cannot verify that ruff/flake8 and Black have been set up in the `code/` directory. The required artifacts are missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/filtered_sequences.csv, data/raw/omnidirector.zip, data/raw/synthetic_omnidirector.zip
- `T008` (rejected 1x): The `ingestion.py` file exists, but the required zip archives (`data/raw/omnidirector.zip` and `data/raw/synthetic_omnidirector.zip`) are missing, so the loader cannot actually read any data. Moreover, the code only reads a CSV inside the zip and does not implement extraction of the grid‑video pairs required by the task. The implementation therefore does not fulfill the specification.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/filtered_sequences.csv
- `T017` (rejected 1x): The repository lacks the required `data/processed/filtered_sequences.csv` file, so the solver cannot consume the intended dataset. Moreover, `code/geometry/solver.py` contains only parsing utilities and placeholder constants; there is no implementation of a CPU‑based `solvePnP` call or generation of relative motion vectors. Both the input data and the core solver functionality are missing.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/poses_estimated.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

