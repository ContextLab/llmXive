# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`code/`, `tests/`, `data/raw/`, `data/processed/`, `state/`) is provided; the artifact list is empty, so the task’s requirement is not satisfied.
- `T001b` (rejected 1x): No `.gitignore` file content was presented; the required file excluding `data/raw/*.nii*`, `data/processed/*.csv`, `__pycache__`, `*.pyc`, and `env/` is missing. The implementer must supply a non‑empty `.gitignore` with those patterns.
- `T001c` (rejected 1x): No `README.md` file was presented in the evidence, and thus the required skeleton with a project title and empty installation/usage sections is missing. The implementer must add a non‑empty `README.md` containing at least the title and placeholder sections for installation and usage.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) are present, and the provided artifacts relate only to the research pipeline, not to the requested linting setup. The task therefore remains unfulfilled.
- `T008` (rejected 1x): No code, scripts, or documentation for memory‑efficient streaming of large NIfTI files is present; the claim lacks any artifact demonstrating that the utilities exist or that they keep RAM usage under 7 GB. The required implementation and evidence are missing.
- `T009` (rejected 1x): The implementer supplied only a high‑level feature specification for data ingestion and analysis; no files, scripts, or configuration related to “Setup environment configuration management for OpenNeuro credentials” are present. The required artifact (e.g., a configuration file, secret‑management script, or documentation showing how OpenNeuro credentials are stored and accessed) is missing.
- `T013b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/session_validation_metrics.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

