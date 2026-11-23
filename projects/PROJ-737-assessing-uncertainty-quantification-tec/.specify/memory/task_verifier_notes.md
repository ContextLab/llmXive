# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The schema YAML correctly lists the eight required columns and the test script passed (exit 0), but `quickstart.md` contains a placeholder for a required fact: the training cap reads "**[deferred] samples**" instead of documenting the 2000-sample cap. The task explicitly requires the document to state the 2000-sample training cap, so this is an unmet requirement that must be fixed.
- **T002** — Requested task execution failed; rerun successfully: code/tests/test_download.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T004** — Checked `code/pipeline.py` (exists) and the result files. `data/results/per_sample_errors.csv` is present but contains only the header (no rows), and the required files `data/results/uq_methods.csv`, `data/results/pipeline_log.csv`, and `data/results/cost_metrics.csv` are missing. Consequently the integration test fails and the pipeline does not satisfy the task’s requirements. The next implementer must run the pipeline to generate all four CSVs with full content (including ≥200 test samples per dataset and entries for every dataset‑method pair) and ensure they conform to the specified schemas
- **T005** — Requested task execution failed; rerun successfully: code/metrics/generate_metrics_raw.py exit=1; code/main.py exit=1
