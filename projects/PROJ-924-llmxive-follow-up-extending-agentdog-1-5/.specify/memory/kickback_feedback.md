# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The `pyproject.toml` file is present and contains Black and Ruff configuration, but the required `.ruff.toml` file does not exist in the project directory. The task explicitly demanded creation of both `pyproject.toml` and a separate `.ruff.toml`; the missing file means the linting configuration is incomplete.
- `T011` (rejected 1x): The evidence does not include a `config.py` file at `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, nor any test output showing that `test_config.py` passed. Consequently, the required constants (`RANDOM_SEED=42`, `MAX_RAM_GB=7`, `BATCH_SIZE=64`) have not been demonstrated to exist. The implementer must add the file with the specified contents and ensure the pytest suite succeeds.
- `T012a` (rejected 1x): No `data_loader.py` file with `fetch_advbench` and `fetch_hf4` implementations is provided, nor any test output showing `test_data_loader.py` passing. Consequently the required functions, error handling, and streaming behavior cannot be verified. The task remains unfinished.
- `T015` (rejected 1x): No evidence was provided that a `checksums.json` file exists in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/`, nor any content showing it contains raw‑data checksums. The required artifact is missing or not shown, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

