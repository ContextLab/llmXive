# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The `src/requirements.txt` and `code/requirements.txt` files differ in size and SHA‑256 hash (154 bytes vs 153 bytes), so they are not byte‑identical as required, and there is no evidence that `pip install -r …` succeeded for either file. The task therefore remains incomplete.
- **T015** — The `quickstart.md` file exists and contains the required commands, but there is no evidence (e.g., execution logs, test run output) showing that `python -m src.pipeline.run_all` and `pytest src/tests/` actually run successfully. Execution proof is needed to satisfy the task.
- **T001** — Requested task execution failed; rerun successfully: code/run_ingest.sh exit=1; code/run_pipeline.sh exit=1
