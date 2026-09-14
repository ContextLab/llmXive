# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listing or file tree was provided showing the required folders (`code/`, `code/ingest`, `code/features`, `code/models`, `code/viz`, `code/utils`, `tests/`). Without concrete evidence that these directories exist, the task requirement is not satisfied.
- `T001b` (rejected 1x): No evidence of the required directories (`data/raw`, `data/processed`, `data/artifacts`) is present; the implementer did not provide any file system artifact or screenshot confirming the directory structure exists. The task remains undone.
- `T001c` (rejected 1x): No evidence of a `state/` directory (or any listing showing its existence) is provided; the implementer’s claim cannot be verified. The required project directory structure is missing from the artifacts.
- `T002a` (rejected 1x): No `__init__.py` files or directory listings were presented, so we cannot verify that they exist in every `code/` and `tests/` subdirectory as required. The implementer must supply the actual file structure showing the created `__init__.py` files.
- `T002b` (rejected 1x): No `.gitignore` file was presented in the evidence, and thus we cannot verify that it contains the required exclusion patterns (`data/raw/*`, `data/processed/*`, `data/artifacts/*`, `*.pyc`, `__pycache__`, `state/*.yaml` except `state/PROJ-485/*.yaml`). The required artifact is missing.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `.flake8` config) or related setup scripts are present in the provided evidence. The only artifacts shown relate to alloy data processing, not to configuring ruff/flake8/black, so the task requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

