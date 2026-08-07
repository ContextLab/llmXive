# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No artifact showing a `src/` directory at the repository root was provided; the evidence list is empty, so we cannot confirm that the required directory exists. The implementer must add the `src/` folder (non‑empty) to satisfy task T001.
- `T001b` (rejected 1x): No evidence of a `tests/` directory at the repository root was provided; the artifact list is empty, so we cannot confirm that the required directory exists or contains any test files. The implementer must add the `tests/` folder (with at least one test file) to satisfy the task.
- `T001c` (rejected 1x): No evidence of the required `data/`, `results/`, or `specs/` directories is provided; the implementer did not include any artifact showing that these folders exist at the repository root. The task remains undone until the directories are created and visible.
- `T001d` (rejected 1x): No evidence was provided that the `data/raw/` and `data/processed/` directories actually exist in the repository; the response contains only the task description and no file listings or screenshots showing those subfolders. The implementer must create the two directories (and ensure they are non‑empty or at least present) for the task to be considered complete.
- `T003` (rejected 1x): I looked for linting/formatting configuration artifacts (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8` or equivalent) and any setup scripts, but none were presented. Without those files the task of configuring ruff/flake8 and Black is not demonstrated. The implementer must add the actual configuration files and ensure they are non‑empty and correctly set up.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: state/projects/PROJ-369-evaluating-the-robustness-of-statistical.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

