# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory tree (`projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/...`) was provided; the implementer did not supply a listing, screenshot, or any file‑system artifact confirming that the specified folders exist. The task cannot be considered complete until the full project structure is created and verified.
- `T002` (rejected 1x): The required file `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/requirements.txt` does not exist; only a top‑level `requirements.txt` is present, which does not meet the specified location requirement. The task therefore remains unfinished.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or setup scripts are present in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied. The implementer must add the appropriate configuration files and ensure they are integrated into the project's workflow.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

