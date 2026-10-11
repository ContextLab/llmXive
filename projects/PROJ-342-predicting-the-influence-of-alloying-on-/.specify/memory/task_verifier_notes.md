# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Missing the required `artifacts/models/`, `artifacts/metrics/`, and `artifacts/reports/` directories, and the `logs/` folder is not shown to exist. The `tests/test_resource_monitor.py` test fails because the decorator does not create `data/resource_usage.json` at the expected location (the file present has a runtime of 0.0 seconds, indicating the dummy function was never actually executed). These gaps mean the task’s verification criteria are not met.
- **T002** — Requested task execution failed; rerun successfully: code/ingest.py exit=1
