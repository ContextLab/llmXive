# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The `quickstart.md` file exists and correctly lists `python -m src.pipeline.run_all` and `pytest src/tests/`, but the test `src/tests/test_quickstart.py` shows that running the pipeline command exits with code 1 (fails to download the Corrosion.csv dataset), so the documented commands do not successfully execute. The pipeline must be fixed (e.g., provide a valid dataset URL or local fallback) for the quickstart to meet the task requirement.
- **T001** — Requested task execution failed; rerun successfully: code/run_ingest.sh exit=1; code/run_pipeline.sh exit=1
