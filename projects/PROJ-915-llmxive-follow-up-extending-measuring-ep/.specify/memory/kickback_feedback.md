# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the `projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/` directory or any of its expected sub‑folders/files is provided; the claim lacks the required project‑structure artifact.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) are presented, nor any evidence that ruff/flake8 and Black have been set up in the repository. The required artifacts are missing, so the task is not satisfied.
- `T004` (rejected 1x): No evidence of the required directories (`data/raw`, `data/processed`, `data/interim`, `data/results`, `code/`, `tests/`) is provided; the implementer did not supply a directory listing, screenshots, or any files showing that the structure has been created. The task remains undone until the specified folders are present and non‑empty.
- `T008` (rejected 1x): No code, configuration files, or documentation for an error‑handling framework (e.g., retry logic for dataset download or timeout handling for inference) were provided. Without any artifact to inspect, we cannot confirm that the required setup was implemented.
- `T017b` (rejected 1x): The required output file `data/interim/human_pilot_cleaned.csv` is absent, and the provided `code/annotation.py` contains unrelated data‑loading and correlation functions rather than the specified cleaning logic (removing raters with <80 % agreement and failing when fewer than 50 rows remain). Both the artifact and its behavior do not meet the task requirements.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

