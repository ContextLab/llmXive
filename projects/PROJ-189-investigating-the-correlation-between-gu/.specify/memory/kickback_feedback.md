# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required root directory `projects/PROJ-189-investigating-the-correlation-between-gu/` being present on disk is provided; the implementer only supplied a textual description without any actual file or folder artifact. The task therefore remains unfulfilled.
- `T001b` (rejected 1x): No evidence of the required subdirectories (`data/raw`, `data/processed`, `data/models`, `code`, `code/utils`, `tests`, `tests/contract`, `tests/integration`, `tests/unit`, `docs`) is presented; the implementer provided no directory listing, screenshots, or other proof that these folders exist and are non‑empty. The task therefore remains unverified.
- `T001c` (rejected 1x): No .gitignore file or its contents were provided; therefore we cannot verify that it contains the required patterns (`data/raw/*`, `__pycache__/`, `venv/`). The implementer must add a .gitignore with those entries.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black` settings) or setup scripts are present in the provided evidence, so the requirement to configure ruff and black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- `T009` (rejected 1x): No configuration file (e.g., YAML/JSON) or code for loading dataset paths and random seeds is present in the provided evidence. The task required tangible artifacts that define and manage these settings, which are missing.
- `T017` (rejected 1x): No code, script, test output, or documentation was provided showing a validation step that checks and removes null values from the final analysis dataset. Without such an artifact, we cannot confirm that the requirement “Add validation to ensure no null values remain in the final analysis dataset” has been met. The implementer must supply the validation implementation (e.g., a function or pipeline step) and evidence (e.g., logs, test results) that the final dataset contains zero nulls.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

