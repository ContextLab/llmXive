# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T100** — The script writes the report to `results/data_feasibility_report.json` instead of the required `data/results/data_feasibility_report.json`, and it always exits with code 0 even when the verdict is `"halt"`—the task mandates a non‑zero exit in that case. These mismatches must be fixed.
- **T101** — Requested task execution failed; rerun successfully: code/data/ingest.py exit=1; code/main_pipeline.py exit=1
