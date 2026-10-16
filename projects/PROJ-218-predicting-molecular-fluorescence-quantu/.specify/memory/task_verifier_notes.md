# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `data/raw/` files, `checksums.txt`, `code/config/seeds.yaml`, and `results/seeds.json` all exist and the download logs show matching SHA‑256 hashes and successful exits. However, there is no evidence that a seed‑configuration module is imported and that it asserts equality with `results/seeds.json` before any stochastic operation (e.g., a shuffle or split), as required by the task. This import/assertion step is missing.
- **T002** — Requested task execution failed; rerun successfully: src/preprocessing/join.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/preprocessing/graph_features.py exit=1
