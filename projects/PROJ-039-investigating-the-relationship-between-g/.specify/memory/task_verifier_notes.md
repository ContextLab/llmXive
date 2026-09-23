# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — No utility functions for SHA256 checksum verification are present, and the required `artifacts/checksums.txt` file (listing checksums for all files in `data/`) is missing or empty. The implementer has not provided any code or generated file to satisfy the task.
- **T012** — The repository contains a `preprocess_microbiome.py` script, but it is truncated and does not show any QIIME2 processing, pseudocount application, SHA256 checksum handling, or creation of `data/processed/microbiome_features.csv`. Moreover, the required output CSV file is absent. The task’s core deliverables are therefore not present.
- **T013** — The provided `code/preprocess_eeg.py` is truncated, contains placeholder logic that raises errors, and does not implement the full preprocessing pipeline (filtering, ICA, epoching, alpha‑power computation, subject‑level filtering). Moreover, the required output file `data/processed/eeg_features.csv` is absent. The task’s deliverables are therefore not met.
