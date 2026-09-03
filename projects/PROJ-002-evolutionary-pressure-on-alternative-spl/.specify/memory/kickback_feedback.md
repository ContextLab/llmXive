# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`src/`, `tests/`, `config/`, `data/`, `results/`, `docs/`) is provided; the implementer did not supply any artifact showing the project structure. The task remains undone.
- `T001c` (rejected 1x): No evidence of the required `tests/unit/`, `tests/integration/`, or `tests/contract/` directories being present was provided; the response contains only the task description and specifications, with no actual filesystem artifacts. The implementer must create and show these three test directories (non‑empty or at least existent) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a `pre-commit` hook) are present, nor any logs or documentation showing that flake8 and Black have been integrated into the project. The provided artifacts relate to a completely different feature (RNA‑seq pipeline) and do not address the linting task at all. The required linting setup is missing.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logger.py
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/hash.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

