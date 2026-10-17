# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quickstart.md file exists and contains the required “Run the end‑to‑end pipeline” section, but the integration test file `tests/integration/test_end_to_end.py` and the configuration file `config.yaml` are missing, and there is no evidence that `pytest -q tests/integration/test_end_to_end.py` passes or that `python -m src.run_pipeline --config config.yaml` runs successfully and prints “Pipeline completed”. These artifacts and execution evidence must be provided to satisfy the task.
- **T002** — Requested task execution failed; rerun successfully: src/curators/curate_failed_figures.py exit=1
