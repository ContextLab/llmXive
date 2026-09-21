# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The claim provides no evidence of the required directories (`code/`, `tests/`, `data/raw`, `data/processed`) being present or populated; no file listings or screenshots are supplied. Without concrete artifacts showing the project structure, the task requirement is not satisfied.
- `T003` (rejected 1x): The repository contains no linting or formatting configuration files (e.g., `.flake8`, `.pylintrc`, `pyproject.toml` with Black settings, or `isort.cfg`) and no evidence of these tools being set up in CI. To satisfy T003, the implementer must add the appropriate configuration files and ensure the tools run as part of the development workflow.
- `T011` (rejected 1x): No `tests/integration/` directory or any test files were presented, and there are no mock FASTQ files or test code shown that would verify the pipeline flow. The required integration test scaffolding is missing entirely.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

