# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt` exists and lists all seven required packages, but none are pinned to a version (no `==` constraints), whereas the task explicitly requires pinned dependencies with a compatible major version. Fix by pinning each package (e.g., `pandas==2.2.x`, `numpy==1.26.x`, etc.) using versions verified compatible with the project's Python environment.
- **T008** — Requested task execution failed; rerun successfully: code/ingestion.py exit=1
- **T011b** — declared artifact(s) missing/empty/invalid: data/processed/legacy_metrics.json
- **T013** — declared artifact(s) missing/empty/invalid: data/processed/metrics.json
