# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/data/real_ingest.py` writes its status JSON to `data/real_ingest_status.json` instead of the required `data/logs/real_ingest_status.json`, and the expected schema files (`*_schema.yaml`) are not present, so `code/run_quickstart_test.py` cannot actually validate the outputs against a schema. Additionally, there is no evidence that the quick‑start test script runs successfully (the recorded pytest run shows a failure). These issues must be fixed for the task to be considered complete.
- **T002** — Requested task execution failed; rerun successfully: code/data/run_synthetic_generator.py exit=1
