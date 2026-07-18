# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listing or file tree was provided showing the required folders (`code/`, `code/ingest`, `code/features`, `code/models`, `code/viz`, `code/utils`, `tests/`). Without concrete evidence that these directories exist, the task requirement is not satisfied.
- **T001b** — No evidence of the required directories (`data/raw`, `data/processed`, `data/artifacts`) is present; the implementer did not provide any file system artifact or screenshot confirming the directory structure exists. The task remains undone.
- **T001c** — No evidence of a `state/` directory (or any listing showing its existence) is provided; the implementer’s claim cannot be verified. The required project directory structure is missing from the artifacts.
- **T002a** — No `__init__.py` files or directory listings were presented, so we cannot verify that they exist in every `code/` and `tests/` subdirectory as required. The implementer must supply the actual file structure showing the created `__init__.py` files.
- **T002b** — No `.gitignore` file was presented in the evidence, and thus we cannot verify that it contains the required exclusion patterns (`data/raw/*`, `data/processed/*`, `data/artifacts/*`, `*.pyc`, `__pycache__`, `state/*.yaml` except `state/PROJ-485/*.yaml`). The required artifact is missing.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `.flake8` config) or related setup scripts are present in the provided evidence. The only artifacts shown relate to alloy data processing, not to configuring ruff/flake8/black, so the task requirement is unmet.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv
