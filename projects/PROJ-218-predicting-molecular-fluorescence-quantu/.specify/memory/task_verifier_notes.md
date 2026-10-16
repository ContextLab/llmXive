# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — `data/raw/` contains only `checksums.txt` — the actual dataset files (`smiles.parquet`, `fqy.json`) referenced by the checksums are missing, so checksums cannot be verified against real data. There is also no download script artifact or evidence of a successful (exit 0) download run, and no seed-configuration module shown that is imported before any shuffle/split call.
- **T002** — Requested task execution failed; rerun successfully: src/preprocessing/join.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/preprocessing/graph_features.py exit=1
