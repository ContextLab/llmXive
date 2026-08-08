# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `data/logs/`, `scripts/`) is provided; the claim cannot be verified without seeing the actual filesystem.
- **T002b** — No evidence of a `venv` directory, activation scripts, or an installed `requirements.txt` (or similar) is present; the claim provides only a textual statement without any accompanying files or logs showing the virtual environment creation or package installation.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or any related setup scripts) were presented, nor any evidence that ruff and black have been integrated into the project. Without these artifacts, the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- **T005b** — The required artifact `data/baseline_saa_raw.json` does not exist, so the scalar SAA mean value cannot be verified as documented. The task’s core deliverable is missing.
- **T007** — The required file `code/baseline_ref.py` is missing entirely, so there is no implementation that loads the JSON or defines the specified schema. Only the JSON data file exists, but without the corresponding Python module the task is not fulfilled.
- **T009** — No environment configuration files, scripts, or documentation (e.g., `environment.yml`, `Dockerfile`, `requirements.txt` with CPU‑only flags) are present to demonstrate that a CPU‑only execution environment has been set up. The provided spec discusses a downstream text‑only pipeline but offers no concrete artifacts that satisfy the “setup environment configuration management for CPU‑only execution constraints” requirement.
- **T019** — declared artifact(s) missing/empty/invalid: data/results/text_pipeline_results.json
- **T025** — declared artifact(s) missing/empty/invalid: data/results/saa_summary.json
