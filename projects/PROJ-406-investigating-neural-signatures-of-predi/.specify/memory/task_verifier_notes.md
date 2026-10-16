# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The two required files exist with correct, non-stub content (`set_global_seed(42)` seeding `random`, NumPy, and `PYTHONHASHSEED`, plus package-load seeding in `src/__init__.py`). However, the task's explicit verification step — running `python -c "import src, numpy as np; src.utils.seed.set_global_seed(42); print(np.random.rand())"` twice and capturing/asserting identical outputs — has no execution evidence anywhere in the packet, so deterministic behavior is claimed but not demonstrated. Provide the captured outputs of the two runs (e.g., a log or test artifact showing identical values) to co
- **T001** — Requested task execution failed; rerun successfully: src/ingest/load_illusions.py exit=1
