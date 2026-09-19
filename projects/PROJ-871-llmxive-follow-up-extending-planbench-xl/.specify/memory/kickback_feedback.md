# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/requirements.txt
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, pre‑commit hooks, or documentation of how flake8/black are set up) are present in the `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/` directory. The implementer provided only the task description and specifications, but no concrete artifacts that configure or enable flake8/black, so the requirement is not satisfied.
- `T007` (rejected 1x): No evidence of the required `data/raw`, `data/derived`, `data/logs`, `data/results` directories or a `.gitignore` file was provided; without these artifacts the task’s deliverable is not satisfied.
- `T009a` (rejected 1x): The provided `injector.py` stops mid‑function (the `inject_failures` implementation is truncated and never writes the modified records to `data/derived/implicit_failure_subset.jsonl`). Moreover, the required output file `data/derived/implicit_failure_subset.jsonl` does not exist. The task’s core requirements—injecting deterministic error patterns, adding the `injected_error` flag, and persisting the result—are therefore not satisfied.
- `T009b` (rejected 1x): The required `data/derived/implicit_failure_subset.jsonl` file is absent, so the indexer cannot parse any data. Moreover, `code/dataset/indexer.py` is truncated and never writes `failure_signatures.json`; the existing `failure_signatures.json` appears pre‑made and does not follow the specified schema (e.g., mixed recovery strategies). Hence the task’s core functionality is not implemented.
- `T010` (rejected 1x): The test file `tests/unit/test_loader.py` is present, but the required data file `data/derived/implicit_failure_subset.jsonl` does not exist, causing the fixture to fail and the contract test to be unusable. The missing dataset prevents the test from verifying the loader as required.
- `T013` (rejected 1x): The `run_baseline.py` script exists, but the required input file `data/derived/implicit_failure_subset.jsonl` is missing, and consequently the expected output log `data/logs/baseline_execution.jsonl` was never created. Without the input dataset the runner cannot execute, so the task is not genuinely fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

