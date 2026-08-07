# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or a pre‑commit hook) are present in the specified project directory, nor any evidence that ruff/black have been set up. The required artifacts are missing.
- `T011` (rejected 1x): The claim provides no visible `config.py` file in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, nor any evidence that `test_config.py` runs and passes. Without the file containing the required constants (`RANDOM_SEED=42`, `MAX_RAM_GB=7`, `BATCH_SIZE=64`) and a passing test, the task is not satisfied. The implementer must add the file with the exact contents and ensure the pytest suite succeeds.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

