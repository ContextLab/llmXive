# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016** — declared artifact(s) missing/empty/invalid: data/processed/subgraph_with_clusters.parquet
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/final_analysis_dataset.parquet
- **T037** — The integration test file exists, but it does **not** use the required input `data/processed/final_analysis_dataset.parquet` (the file is missing) and instead relies on a synthetic fixture. Consequently the test does not truly validate the pipeline on the real dataset, nor can we confirm it checks corrected p‑values and the “associational” label. The missing dataset (and likely incomplete test logic) must be provided for the task to be satisfied.
