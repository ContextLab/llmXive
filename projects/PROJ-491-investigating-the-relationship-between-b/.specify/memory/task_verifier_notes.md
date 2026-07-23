# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`code/`, `tests/`, `data/raw/`, `data/processed/`, `state/`) is provided; the artifact list is empty, so the task’s requirement is not satisfied.
- **T001b** — No `.gitignore` file content was presented; the required file excluding `data/raw/*.nii*`, `data/processed/*.csv`, `__pycache__`, `*.pyc`, and `env/` is missing. The implementer must supply a non‑empty `.gitignore` with those patterns.
- **T001c** — No `README.md` file was presented in the evidence, and thus the required skeleton with a project title and empty installation/usage sections is missing. The implementer must add a non‑empty `README.md` containing at least the title and placeholder sections for installation and usage.
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) are present, and the provided artifacts relate only to the research pipeline, not to the requested linting setup. The task therefore remains unfulfilled.
- **T007c** — declared artifact(s) missing/empty/invalid: data/contracts/Power264_excl_vs_nodes.json
- **T008** — No code, scripts, or documentation for memory‑efficient streaming of large NIfTI files is present; the claim lacks any artifact demonstrating that the utilities exist or that they keep RAM usage under 7 GB. The required implementation and evidence are missing.
- **T009** — The implementer supplied only a high‑level feature specification for data ingestion and analysis; no files, scripts, or configuration related to “Setup environment configuration management for OpenNeuro credentials” are present. The required artifact (e.g., a configuration file, secret‑management script, or documentation showing how OpenNeuro credentials are stored and accessed) is missing.
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/session_validation_metrics.json
- **T013c** — declared artifact(s) missing/empty/invalid: data/processed/excluded_session_ids.csv
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/ingestion_warnings.log
