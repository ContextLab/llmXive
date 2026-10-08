# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/raw/`, `data/processed/`, `tests/`, `state/`, `docs/`) is provided; the implementer did not supply any artifact showing that the project structure was created.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with black settings, or CI scripts invoking these tools) are present. The provided artifacts relate only to the scientific feature specification and contain no evidence that ruff/flake8 and black have been set up. The task therefore remains unfulfilled.
- `T005` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `code/data/`, `code/preprocess/`, `code/analysis/`, `code/modeling/`, `code/validation/`, `code/report/`, `tests/`) is present; the implementer did not supply any file‑system listing or screenshots showing the structure. The task remains undone.
- `T011` (rejected 1x): No evidence of a script or workflow that checks T010’s result, determines a verified URL, downloads the EDS maps from that URL and Zenodo, and saves them to `data/raw/`. The required raw files or any log showing the conditional behavior are absent, so the task’s core requirement is not satisfied.
- `T014c` (rejected 1x): The required output file `data/processed/unified_dataset.csv` is absent, and the provided `code/data/ingest.py` is incomplete (truncated) and does not contain logic to generate the unified CSV with the specified columns. The task’s core deliverable is therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

