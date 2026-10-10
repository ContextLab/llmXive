# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The provided `io.py` and `logging.py` contain the required functions and a module‑level logger, but the unit tests import them as `utils.io` and `utils.logging`. The repository only has a `code/utils` package, not a top‑level `utils` package, so the imports will fail (ModuleNotFoundError) and the tests cannot verify the functionality. The import path must be corrected (e.g., expose a top‑level `utils` package or adjust the tests) for the task to be considered complete.
- **T005** — Requested task execution failed; rerun successfully: code/ingestion/download_ace.py exit=1; code/ingestion/download_noaa.py exit=1
