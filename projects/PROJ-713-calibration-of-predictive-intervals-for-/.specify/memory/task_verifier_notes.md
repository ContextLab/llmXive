# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The `code/` directory and the log showing `create_code_dir.py` ran without error are present, but the actual contents of `create_code_dir.py` were not examined. The task requires the script to create the directory idempotently using `parents=True, exist_ok=True` and to assert `os.access('code', os.W_OK)`. Without seeing the script (or a test confirming those exact calls and the write‑access assertion), we cannot verify that the implementation meets the specification. Provide the script’s source code (or a test run that demonstrates the required behavior) to complete the task.
- **T001f** — Requested task execution failed; rerun successfully: code/verify_config.py exit=1
