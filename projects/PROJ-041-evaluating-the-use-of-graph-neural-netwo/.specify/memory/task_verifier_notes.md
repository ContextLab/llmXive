# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project layout directories, `requirements.txt`, `pyproject.toml`, `seed.py` and `memory_monitor.py` exist, but the provided test suite shows failures: the layout‑creation script is not found at the expected path and the seed reproducibility test errors out because `numpy` isn’t imported. Moreover, there is no evidence that `seed.set_seed(42)` actually produces a reproducible RNG state, that `run_with_limit` raises `MemoryLimitError` for a >7 GB allocation, or that a sample JSON validates against the `contracts/*.schema.yaml` files. These missing or failing checks mean the task is not fully
- **T002** — Requested task execution failed; rerun successfully: code/data/download_ctu13.py exit=1
