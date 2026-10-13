# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T100** — The `code/data/feasibility.py` script creates the required JSON report, but it **always exits with status 0**, violating the task requirement that the script must exit with a non‑zero code when the verdict is `"halt"` (no linked EDS maps). This mismatch means the implementation does not fully satisfy the specification.
- **T101** — Requested task execution failed; rerun successfully: code/data/ingest.py exit=1; code/main_pipeline.py exit=1
