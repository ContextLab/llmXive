# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure evidence (e.g., listings or screenshots of `data/raw/`, `data/processed/`, `code/`, `outputs/`, `tests/`) was provided, so we cannot confirm the required folders exist. The implementer must supply proof that these directories have been created.
- `T001b` (rejected 1x): No evidence of the required directory `projects/PROJ-540-the-influence-of-social-media-doomscroll/` or any `__init__.py` files was provided; the claim lacks any artifact showing the source structure exists. The implementer must create the folder and include the `__init__.py` files.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or equivalent) are present in the provided evidence, and the only artifacts shown relate to a different research feature. Consequently the requirement to configure flake8/black is not satisfied.
- `T014` (rejected 1x): No code, configuration, or log files were provided that demonstrate logging of row counts, missing‑value statistics, or power‑check results. The claim lacks any tangible artifact showing the required logging functionality was added.
- `T020` (rejected 1x): No code, data, or output files were supplied; there is no evidence of a data‑ingestion script, variable extraction, regression model, diagnostics, or visualization required by the user stories. Consequently the required artifacts are missing, so the task is not genuinely completed.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: outputs/correlation_results.json
- `T029` (rejected 1x): declared artifact(s) missing/empty/invalid: outputs/plot.png

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

