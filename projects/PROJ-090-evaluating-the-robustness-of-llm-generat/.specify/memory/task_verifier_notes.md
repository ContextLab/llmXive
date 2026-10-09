# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The quickstart.md file exists and documents the required command, but there is no evidence (e.g., a terminal log, timing report, or test script output) showing that `python -m code.main --run-sample` actually finishes within 30 seconds and prints “Sample run completed”. Execution proof is needed to satisfy the verification condition.
- **T004** — The repository contains `code/utils/logging.py` with a `setup_logger()` that is designed to write JSON‑lines to `data/logs/app.log`, but the required log file `data/logs/app.log` is missing—no evidence shows the function was executed to create it, nor that any JSON line was written. The task is not satisfied until the logger is invoked and the file with at least one JSON entry is present.
- **T008a** — Requested task execution failed; rerun successfully: code/utils/generate_perturbation_schema.py exit=1
