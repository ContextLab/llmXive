# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The confirmed artifacts (`code/requirements.txt` with all pinned dependencies, `code/utils/models.py` with real dataclasses, and the quickstart documenting runnable commands) satisfy those portions. However, the task also requires a logging configuration and an `.env.example` containing `GITHUB_TOKEN`, `DATA_PATH`, and `LOG_PATH`, and neither artifact appears in the evidence — the quickstart merely references `.env.example` without it existing on disk. The implementer must add the logging config (e.g., `code/utils/logging_config.py` or equivalent) and a `.env.example` with those three variable
- **T002** — Requested task execution failed; rerun successfully: code/01_data_curation.py exit=1
