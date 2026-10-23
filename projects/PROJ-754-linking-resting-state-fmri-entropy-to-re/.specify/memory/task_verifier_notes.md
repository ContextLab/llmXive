# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project lacks the required `code/src/pipeline.py` (the orchestrator function `run_pipeline` is never imported) and the `src` shim does not expose `run_pipeline`, causing the integration test `test_run_pipeline.py` to error. The pytest suite therefore does not finish with “0 failed, X passed”. Additionally, the quick‑start command prints “Pipeline completed successfully…” instead of the exact required “Pipeline completed”. These missing/incorrect artifacts must be added and corrected for the task to be complete.
