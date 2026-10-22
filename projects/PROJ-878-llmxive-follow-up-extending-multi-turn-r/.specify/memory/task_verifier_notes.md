# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The test file exists and its content matches the task (schema validation of SyntheticPuzzle plus the |r| < 0.2 orthogonalization check on the generated dataset), but the recorded execution log shows `pytest code/tests/test_graph_generator.py` failed with exit code 2 — collection aborted on an ImportError (`pyarrow requires NumPy 2.0 or newer, found 1.24.3`) triggered by `from datasets import load_dataset` in `code/graph_generator.py`. The task's verification criterion is that the tests pass after T003, and there is no evidence of any successful run; the implementer must fix the dependency/impo
- **T003** — Requested task execution failed; rerun successfully: code/graph_generator.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/rm_executor.py exit=1
