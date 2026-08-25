# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001b` (rejected 1x): The required output file `data/raw/era_sample.h5` is missing, and the log does not show any actual validation of hourly resolution or temperature values. The script exists, but there is no evidence it was run successfully to produce the required sample and verification logs.
- `T009` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) or scripts are present in the provided artifacts; the only evidence is a unrelated feature specification, which does not demonstrate that ruff/flake8 and black have been set up.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

