# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing or file contents were provided, so there is no evidence that `projects/PROJ-721-evaluating-calibration-of-predictive-int/` with the required `code/`, `data/`, `results/`, `tests/`, `contracts/` subfolders and `__init__.py` files actually exists. The implementer must supply the created folder hierarchy and the initialization files.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with `[tool.black]` and `[tool.ruff]`, or `.flake8` and `black` config) are present in the provided evidence, so the requirement to set up `ruff`/`flake8` and `black` is not demonstrated. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly specify the tools.
- `T004` (rejected 1x): No M4‑Dataset.zip, manifest.json, or any checksum‑validation logs are present in the provided evidence, so the required files were not fetched nor their SHA256 checksums verified. The task remains undone.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

