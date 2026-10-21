# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T102** — The `entity_linker.py` file exists and implements the required deterministic linking logic, but it (and the test suite) import `utils.config` and `utils.entity_linker` instead of the correct package path `code.utils.*`. This import mismatch means the module cannot be imported and the pytest tests will fail, so the task’s requirement of a passing test suite is not met. The import statements need to be corrected to use the `code.utils` package (or a top‑level `utils` package must be provided).
- **T103** — Requested task execution failed; rerun successfully: code/ingest/download_data.py exit=1
