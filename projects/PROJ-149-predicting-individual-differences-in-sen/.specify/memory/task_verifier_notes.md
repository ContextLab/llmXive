# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The provided `code/03_extract_features.py` is truncated and never reaches the processing or CSV‑writing steps; it even raises a `FileNotFoundError` if `exclusion_log.csv` is absent, contrary to the requirement to handle a missing/empty file gracefully. Moreover, both `data/interim/exclusion_log.csv` and the required output `data/interim/eeg_psd.csv` are absent. The task’s core functionality and outputs are therefore not delivered.
- **T017** — The required output files `data/interim/split_indices.json` and `data/processed/model_results.json` are not present, and the provided `code/04_modeling.py` is truncated before any logic that would generate or save these files (or fully implement the chunked‑processing requirement). The task’s deliverables are therefore not satisfied.
- **T019** — The required output file `data/processed/model_results.json` is missing, so the Adjusted R² and optimal lambda were not calculated and logged as specified. The task therefore lacks the essential artifact.
- **T022a** — declared artifact(s) missing/empty/invalid: data/interim/split_indices.json, data/processed/model_results.json, data/interim/permutation_null_distribution.npy
- **T022b** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
