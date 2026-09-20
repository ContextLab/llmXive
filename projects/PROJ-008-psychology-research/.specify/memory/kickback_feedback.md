# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or equivalent) are presented, nor any evidence that Ruff and Black have been set up in the repository. The required artifacts are missing.
- `T016` (rejected 1x): The `collector.py` file exists and contains rate‑limiting and backoff logic, but the required log file `data/raw/retrieval_log.json` is missing, so the task’s logging requirement (including a 200‑status entry) is not met. The implementer must create and populate the log file as specified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

