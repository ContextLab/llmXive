# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The pipeline entry point (`code/main.py`) and seed module exist and run, but the required specification files are in the wrong locations and a needed schema file is missing. `specs/001-predict-lst-wear/research.md` and `quickstart.md` are stored under `specs/001-predicting-the-impact-of-laser-surface-t/` instead of the exact `specs/001-predict-lst-wear/` path, causing `test_research.py` to fail. Likewise, `code/config/schema_map.json` is not where `test_schema_map.py` expects (`config/schema_map.json`), and `dataset.schema.yaml` is absent, so the schema‑map test cannot verify that all canonica
- **T002** — Requested task execution failed; rerun successfully: code/ingest.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
