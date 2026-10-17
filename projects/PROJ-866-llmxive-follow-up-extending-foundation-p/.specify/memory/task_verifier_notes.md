# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — I checked `code/main.py` (the orchestrator) and the log showing `python code/main.py --help` exits 0 and lists all flags. However there is no evidence that a full run (e.g., `python code/main.py --generate --compress --analyze --n-workflows 20`) completes successfully, nor any pytest output confirming the test suite passes. Additionally, the required generator (`code/generators/synthetic_workflow.py`) and engine scripts (`code/engines/full_context.py`, `code/engines/compressed_context.py`) are not shown to exist, and the expected output files (`data/processed/full_context_logs.json`, `data/pro
- **T111** — Requested task execution failed; rerun successfully: code/main.py exit=1
