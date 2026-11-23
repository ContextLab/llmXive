# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/` directory exists, but the required `data/raw/`, `data/processed/`, `tests/unit/`, and `tests/integration/` directories are missing from the project structure.
- **T003** — The evidence contains no linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8`), nor any scripts or CI steps that invoke ruff/flake8/black. Without these artifacts, the task of configuring the tools is not demonstrated.
- **T004** — The provided `code/config.py` defines the configuration values as separate variables, not as a single dictionary matching the exact key‑value mapping required, and the `DATASET_ID` string lacks the trailing space shown in the task specification. The artifact therefore does not precisely satisfy the task’s requirement.
- **T005** — The `code/download.py` file exists and implements streaming fetch with exponential‑backoff retries, but it never calls the `verify_checksum` (or `compute_file_checksum`) functions, so SHA‑256 checksum verification is not performed as required. Adding checksum verification of the downloaded dataset (or of each streamed file) is needed to satisfy the task.
