# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T048** — The required output file `data/intermediate/merged.csv` does not exist, and the ingestion pipeline cannot run successfully: `fetch_dft_data` is called without the required `material_ids` argument, and `fetch_experimental_data` does not abort on download failures. Consequently no real merged dataset is produced, and the checksum file is not refreshed. The task’s core deliverables are missing.
