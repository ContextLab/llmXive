# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `src/data/something_loader.py` file correctly uses `load_dataset(..., streaming=True)` and provides a deterministic seed, but the unit test `tests/test_something_loader.py` fails (see execution log) because the HuggingFace dataset `"something-something-v2"` cannot be found, causing a `DatasetNotFoundError`. Consequently the test does not load five videos nor verify non‑empty frames, so the task’s requirements are not met. Fix the dataset identifier or provide a mock/fixture so the test can pass.
- **T004** — Requested task execution failed; rerun successfully: src/data/optical_flow_loader.py exit=1
