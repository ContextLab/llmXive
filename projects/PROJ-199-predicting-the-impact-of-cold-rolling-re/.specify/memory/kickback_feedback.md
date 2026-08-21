# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required top‑level directories (`code/`, `data/`, `tests/`, `docs/`) is provided; the implementer did not supply a directory listing or any files showing that these folders exist. The task remains undone until those directories are created and visible.
- `T001b` (rejected 1x): No `.gitignore` file is present in the provided evidence; the implementer did not supply the required artifact listing Python, data, and IDE patterns. The task remains undone.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .flake8, pyproject.toml with black settings, pre‑commit hooks) are present, nor any documentation showing that flake8/black have been set up and integrated into the project. The provided material only describes a scientific feature and does not include the required linting setup.
- `T004` (rejected 1x): No directory structure or `.gitkeep` files were presented as evidence; without visible `data/raw/.gitkeep`, `data/processed/.gitkeep`, and `data/interim/.gitkeep` we cannot confirm the required subdirectories were created.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/download.py
- `T013` (rejected 1x): No code, script, or log files were presented that demonstrate added error handling for missing reduction levels or corrupted EBSD files, nor any evidence that warnings are logged and processing continues as required by US‑1 Scenario 3. The implementer provided no tangible artifact to verify the requested functionality.
- `T014` (rejected 1x): No code, script, or documentation implementing the required exclusion logic (flagging samples with >50 % filtered points as “low reliability” and removing them from the final training set) is present in the provided artifacts. The implementer’s claim cannot be verified because the necessary artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

