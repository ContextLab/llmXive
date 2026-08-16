# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005b** — No `.gitignore` file was presented in the evidence, and therefore we cannot confirm that it exists or contains the required exclusions (`data/raw/*`, `data/processed/*`, `data/results/*`, `__pycache__`, `.env`, `*.pyc`, `.pytest_cache`). The implementer must add a non‑empty `.gitignore` with those patterns.
- **T047** — The provided `analysis.py` only checks zero‑inflation at a 30 % threshold, never logs a warning to `data/metadata/method_selection_log.json`, and does not produce a `zero_inflation_warning` flag. Moreover, the required JSON log file is missing entirely. The task’s core requirement (handling >50 % zeros with logging and flagging) is not satisfied.
- **T051** — declared artifact(s) missing/empty/invalid: data/metadata/method_selection_log.json
