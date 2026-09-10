# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — declared artifact(s) missing/empty/invalid: tests/integration/test_data_pipeline.py, data/processed/merged_dataset.csv
- **T012** — The `fetch_viral_genomes` function in `src/download.py` is a stub that raises `NotImplementedError`, so no real NCBI Virus API query, FASTA parsing, or dict output is produced. Moreover, the required `data/manifest_v1.json` file does not exist, and the manifest generation logic does not compute SHA‑256 checksums or follow the exact key schema. The task’s core functionality and manifest output are missing.
- **T013** — The `fetch_geo_data` function is still a stub that raises `NotImplementedError`, so no GEO download or parsing occurs, and no dictionary of sample‑to‑strain accessions is produced. Moreover, the required `data/manifest_v2.json` file does not exist (and the manifest generation code leaves the `checksums` field empty). Both the core function and the manifest output are missing, so the task is not satisfied.
- **T014** — declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/normalized_counts.csv
- **T015** — declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/ortholog_map.csv
