# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence was presented showing that the required directories (`code/`, `data/raw/`, `data/derived/`, `data/processed/`, `tests/`, `state/`) actually exist in the repository; the response contains only the task description and no file‑system listing or screenshots. The implementer must provide a directory tree or similar proof that these folders have been created and are non‑empty.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or CI scripts invoking these tools) were presented, nor any evidence that such tools have been set up in the repository. The required artifacts are missing, so the task is not satisfied.
- `T004` (rejected 1x): No evidence was provided that the required directories (`data/raw/`, `data/derived/`, `data/processed/`) actually exist on disk; the claim is unsupported and the artifact is missing.
- `T007` (rejected 1x): The claim that the files `code/models/Participant.py`, `Stimulus.py`, and `GazeEvent.py` (or equivalent) exist with the required fields cannot be verified because no such files or code snippets were provided. Without the actual model definitions, we cannot confirm that the data models were created as specified. The implementer must add the model files containing the declared attributes.
- `T008` (rejected 1x): No logging configuration files, scripts, or documentation were provided; there is no evidence of a logging infrastructure that captures data‑quality warnings or exclusion counts as required by task T008. The implementer must supply the actual logging setup (e.g., config files, code snippets, or logs) that records these metrics.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

