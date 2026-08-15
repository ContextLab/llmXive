# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was provided that a `code/` directory exists in the repository (e.g., a directory listing or any files inside it). Without such artifact, the requirement “Create `code/` root directory” cannot be confirmed.
- `T004` (rejected 1x): The provided artifacts only describe research user stories for KVarN static prior and contain no configuration files, scripts, or documentation for setting up ruff linting or black formatting (e.g., no `pyproject.toml`, `.ruff.toml`, or CI integration). Consequently, the required linting/formatting setup is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

