# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The provided `code/main.py` excerpt only defines logging, catalog loading, and the public API list; it never shows the core logic for generating code, invoking the LLM, running `pytest --cov`, or writing the required JSON coverage records. Consequently the script does not demonstrably orchestrate generation and coverage execution for a batch of tasks as the task demands. The missing implementation of `process_single_task`, `run_batch_pipeline`, and related functions must be added.
