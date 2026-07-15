# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the listed directories (`code/`, `code/synthetic`, `code/metrics`, etc.) is provided; without a manifest, screenshot, or file‑tree showing these folders, we cannot confirm they were actually created. The implementer must supply concrete proof that the required project structure exists.
- `T001b` (rejected 1x): No `.gitignore` file was presented; the evidence does not include the required file listing the specified exclusions, so the task’s deliverable is missing.
- `T001c` (rejected 1x): No README.md file was presented; the required artifact is missing, so the task of initializing a README with project overview and quickstart instructions has not been fulfilled.
- `T003` (rejected 1x): The implementer provided only the scientific feature specification and no linting/formatting configuration artifacts (e.g., `pyproject.toml` with Black and Ruff settings, a `.flake8` file, or documentation of tool integration). Consequently, the required linting and formatting setup is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

