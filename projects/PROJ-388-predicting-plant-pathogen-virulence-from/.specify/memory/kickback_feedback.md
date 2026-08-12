# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure is presented in the provided evidence; there are no listed files or folder listings showing `src/`, `tests/`, `data/raw`, `data/processed`, `output`, and the subfolders under `src/`. The required folders must be created and visible in the repository for the task to be considered complete.
- `T002` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/config.py
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) or documentation of their integration into the project are present. Consequently, the required artifact to demonstrate that ruff/flake8 and black have been configured is missing.
- `T008` (rejected 1x): The required file `src/models/species_aggregate.py` does not exist, so the class `SpeciesAggregate` with the specified fields is missing entirely. The task’s core artifact is absent, making the implementation incomplete.
- `T010` (rejected 1x): The implementer only asserted that the required directories were created, but no file‑system listing, screenshots, or other concrete evidence of the `data/raw`, `data/processed`, `output`, `src/data`, `src/analysis`, and `src/viz` folders is provided. Without actual artifacts confirming the directory structure exists, the task requirement is not satisfied.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/merge.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

