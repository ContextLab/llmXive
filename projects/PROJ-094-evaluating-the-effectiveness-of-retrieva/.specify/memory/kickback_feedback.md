# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory tree or file list is provided showing that the required folders (`src/data`, `src/models`, `src/analysis`, `src/cli`, `src/lib`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`, `tests/contract`) actually exist. The implementer’s claim lacks concrete evidence, so the task is not verified as completed.
- `T002` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with `[tool.black]` and `[tool.ruff]`, `.ruff.toml`, or similar) were presented. Without concrete artifacts showing that `ruff` and `black` are configured, the claim that the task is completed cannot be verified. The implementer must add the appropriate configuration files to the repository.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/checksum.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

