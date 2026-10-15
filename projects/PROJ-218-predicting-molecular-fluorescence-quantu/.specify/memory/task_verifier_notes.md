# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows only `checksums.txt`, `seeds.yaml`, and `seeds.json` are present; the required raw data files (`smiles.parquet`, `fqy.json`) are missing, and there is no proof that a download script ran successfully or that the seed‑configuration module is imported before any stochastic operation. These artifacts must be added and verified.
- **T002** — Requested task execution failed; rerun successfully: src/preprocessing/join.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/preprocessing/graph_features.py exit=1
