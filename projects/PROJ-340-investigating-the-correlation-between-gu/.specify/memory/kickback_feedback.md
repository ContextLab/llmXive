# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005b` (rejected 1x): No `.gitignore` file was presented in the evidence, and therefore we cannot confirm that it exists or contains the required exclusions (`data/raw/*`, `data/processed/*`, `data/results/*`, `__pycache__`, `.env`, `*.pyc`, `.pytest_cache`). The implementer must add a non‑empty `.gitignore` with those patterns.
- `T047` (rejected 1x): The provided `analysis.py` only checks zero‑inflation at a 30 % threshold, never logs a warning to `data/metadata/method_selection_log.json`, and does not produce a `zero_inflation_warning` flag. Moreover, the required JSON log file is missing entirely. The task’s core requirement (handling >50 % zeros with logging and flagging) is not satisfied.
- `T051` (rejected 1x): declared artifact(s) missing/empty/invalid: data/metadata/method_selection_log.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

