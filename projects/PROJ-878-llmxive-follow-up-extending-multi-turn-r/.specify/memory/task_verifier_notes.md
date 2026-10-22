# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The only execution record (`code/.tasks/T002...log`) shows `pytest` exiting with code 2 — the test module fails to even collect because `code/graph_generator.py` imports `datasets`/`pyarrow`, which is incompatible with the installed NumPy 1.24.3 ("pyarrow requires NumPy 2.0 or newer"). The task's verification criterion — `pytest code/tests/test_graph_generator.py` passes after T003 — is therefore not met, and there is no evidence the generated dataset files (`data/raw/synthetic_puzzles.jsonl`, `data/raw/aux_puzzles.jsonl`) exist for the integration test to validate. Fix: remove or guard the `d
- **T003** — Requested task execution failed; rerun successfully: code/graph_generator.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/rm_executor.py exit=1
