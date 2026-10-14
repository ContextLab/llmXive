# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — Requested task execution failed; rerun successfully: code/R/verify_renv.py exit=1
- **T002** — `code/config.yaml` exists and is valid YAML with the Dryad base URL, AnAge URL, seed 42, and alpha 0.05, but the required dataset IDs are not documented — `dataset_ids: []` with a comment "replace with real IDs after discovery" is an explicit placeholder. Additionally, no evidence was provided that `02_ingest_data.py` and `03_clean_merge.py` exist and read this config (the task's verification criterion), nor that they contain no hard-coded URLs or seeds.
