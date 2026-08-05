# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was presented showing that the required `code/`, `data/raw`, `data/processed`, `results`, and `specs/` directories actually exist in the repository; the claim is unsupported. The implementer must provide a directory listing or screenshots confirming these folders are created.
- `T001b` (rejected 1x): declared artifact(s) missing/empty/invalid: config.yaml
- `T002b` (rejected 1x): No repository, script, or documentation showing that a git repository was initialized or that a Python virtual environment was created was provided; the claim lacks any tangible artifact to verify the required setup.
- `T003` (rejected 1x): The only evidence presented concerns a research pipeline for static analysis tools and contains no configuration files, scripts, or documentation for ruff or black. There is no artifact (e.g., pyproject.toml, .ruff.toml, or black configuration) that demonstrates linting/formatting setup, so the required task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

