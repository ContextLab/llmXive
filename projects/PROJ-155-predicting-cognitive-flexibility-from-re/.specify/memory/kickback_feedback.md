# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): I looked for the required top‑level folders (`code/`, `data/`, `docs/`, `tests/`) but none are present in the provided artifact list or description. Without these directories the project structure specified in `plan.md` has not been created.
- `T003` (rejected 1x): The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `.flake8`), nor any evidence that ruff/flake8 and Black were installed or integrated into the project workflow. Consequently, the requirement to configure these tools is not satisfied. The missing artifacts must be added and demonstrated (e.g., runnable lint/format commands passing without errors).
- `T015` (rejected 1x): The repository lacks the required `data/processed/exclusion_log.csv` file, and the provided `code/utils/motion.py` (as shown) contains only utility functions for calculating mean FD and loading motion parameters—it does not implement the filtering of subjects with Mean FD > 0.2 mm nor write the specified log with the required columns. The task’s deliverable is therefore not satisfied.
- `T015a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/exclusion_log.csv, data/results/regression_summary.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

