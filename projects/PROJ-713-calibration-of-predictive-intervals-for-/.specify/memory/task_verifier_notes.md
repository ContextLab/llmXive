# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree (`code/`, `tests/`, `data/raw/`, `data/processed/`, `results/`) is presented, nor any script showing a retry loop with exponential backoff around `os.path.isdir`. The required artifacts are missing, so the task is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., .flake8, pyproject.toml with Black settings, pre‑commit hooks) are present in the provided evidence; the only artifact shown relates to the predictive‑interval calibration feature, not to the requested linting setup. The required linting configuration is therefore missing.
- **T015** — The provided `code/models/lstm_model.py` contains a fallback mechanism (“Includes fallback to Empirical CDF if intervals are invalid”) which the task explicitly forbids, and it does not implement the required retry‑with‑reduced‑learning‑rate logic nor any logging to `results/skipped_series.log` (the log file is missing). Consequently the task requirements are not fully met.
