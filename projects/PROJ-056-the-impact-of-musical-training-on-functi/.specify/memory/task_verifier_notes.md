# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `code/main.py`, `code/data/run_synthetic_generator.py`, `code/data/real_ingest.py`, and `code/run_quickstart_test.py` for required CLI parsing, script entry‑point, real‑data stub behavior, and quick‑start test logic. While the scripts exist and implement the described behavior, the quick‑start test’s schema validation cannot run because the expected contract files (e.g., `subject.schema.yaml`, `statistical_result.schema.yaml`, `network_component.schema.yaml`) are missing from the repository, so the test does not actually assert schema compliance. Add the missing schema files under `spe
- **T002** — Requested task execution failed; rerun successfully: code/data/run_synthetic_generator.py exit=1
