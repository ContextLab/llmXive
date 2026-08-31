# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or other evidence were provided to show that the required folders (`data/raw`, `data/processed`, `code`, `tests`, `artifacts/logs`, `artifacts/plots`, `artifacts/reports`, `contracts`) were actually created; without such proof the task cannot be confirmed as done.
- `T003b` (rejected 1x): No configuration files (e.g., `pyproject.toml` with ruff/black settings) or command‑line output showing that ruff and black were run on the empty project are present. Consequently there is no evidence that linting/formatting tools were configured or that initial checks verified their validity. The required artifacts are missing.
- `T006` (rejected 1x): No `contracts/` directory or JSON Schema files for `PaperManifest`, `ReproResult`, or `StatSummary` were presented. Without these artifacts, the task of setting up the directory and generating the required schemas is not satisfied.
- `T013` (rejected 1x): The required output file `artifacts/reports/repro_results.json` is missing, and the provided snippet of `code/model_runner.py` does not demonstrate the JSON‑writing step, model‑size substitution logic, or full end‑to‑end training/evaluation flow. Without the report artifact and clear evidence of the required behavior, the task is not genuinely completed.
- `T018` (rejected 1x): The repository contains a `code/main.py` file, but it is truncated and does not show a complete implementation that writes `artifacts/reports/repro_results.json`. Moreover, the required `artifacts/reports/repro_results.json` file is absent, so the aggregation result is not produced. The task’s core output is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

