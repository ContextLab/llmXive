# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/raw`, `data/processed`, `data/models`, `tests/`) is present; the provided material only describes feature specifications and contains no filesystem artifacts. The task’s core deliverable – the project folder structure – is missing.
- `T003` (rejected 1x): No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or pre‑commit hooks) are present in the `code/` directory, nor any evidence that ruff and black have been set up. The required artifact is missing.
- `T012` (rejected 1x): No `tests/unit/` or `tests/integration/` directories (or any files within them) are present in the provided evidence; the implementer did not supply the required directory structure. The task remains undone.
- `T014` (rejected 1x): The repository contains a `code/ingest.py` file, but it is truncated and does not show any logic that reads the source datasets, performs a 5‑km grid merge, and writes `data/processed/reef_species_unified.csv`. Moreover, the required output CSV file is absent from the `data/processed` directory. The core deliverable of the task – a unified CSV produced by the ingestion script – is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

