# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T029d** — The `validator.py` file only defines download functions and a checksum calculator; it never verifies a downloaded file against a stored value nor calls `register_dataset_checksum` to write the checksum into `data/simulation_metadata.json`. The provided `simulation_metadata.json` contains only schema and run metadata and does not include any recorded checksums for the Breast Cancer, Wine, or Adult datasets. The required verification and recording steps are missing.
- **T031** — The required output file `data/simulation/real_data_pvalues.csv` does not exist, so the real-data analyses and saved p‑value distributions are missing. Without this artifact the task’s core requirement is not satisfied.
