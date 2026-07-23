# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (code/, data/, state/, tests/, docs/) is provided; the implementer did not supply any file listings or contents showing that the project structure from `plan.md` has been created. The task remains undone until those folders are present and contain appropriate placeholder or initial files.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with black settings) are present, nor any documentation showing that ruff/flake8 and black have been set up for the project. The provided artifacts relate only to the EEG network‑efficiency feature and do not address the linting/formatting task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

