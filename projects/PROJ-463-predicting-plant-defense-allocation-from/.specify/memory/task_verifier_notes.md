# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `src/`, `tests/`, and `data/` directories (or any files within them) was provided; without a visible project structure we cannot confirm the task was fulfilled.
- **T002** — No `requirements.txt` file or any project initialization artifacts are presented; the evidence contains only the feature specification text, not the requested pinned requirements file or project scaffold. The implementer must add a Python project structure with a `requirements.txt` that lists exact version pins.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or a `ruff` section, or a pre‑commit hook file) are presented, nor any evidence that `ruff` and `black` have been installed or integrated into the project workflow. The required artifacts are missing, so the task is not satisfied.
- **T004** — No `src/utils/config.py` file or any code snippet was provided; therefore the required configuration‑management module for paths, seeds, and thresholds is missing. The implementer must add a non‑empty `config.py` implementing the specified settings.
