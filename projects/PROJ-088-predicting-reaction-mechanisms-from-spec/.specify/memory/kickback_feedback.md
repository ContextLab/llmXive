# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`src/`, `tests/`, `specs/001-predicting-reaction-mechanisms/`, `data/`, `state/projects/`) is provided; the claim lacks any artifact listing or screenshots confirming their existence. The implementer must supply a directory listing or similar proof that these folders have been created and are non‑empty.
- `T001b` (rejected 1x): No `__init__.py` files are presented for any of the `src/` or `tests/` subdirectories; the claim lacks any artifact evidence showing those files exist or contain appropriate package initialization code. The required package marker files are missing.
- `T003` (rejected 1x): No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, `black.toml`, or a `pre-commit` config) are present in the provided evidence, so the requirement to set up ruff/flake8 and black has not been demonstrated. The implementer must add the actual configuration artifacts and show they are functional.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logging.py
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/io.py
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/seed.py
- `T033a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/dft_setup.py, data/reference/literature_db.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

