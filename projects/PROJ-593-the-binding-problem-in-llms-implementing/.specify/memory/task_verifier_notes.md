# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided evidence contains only a feature specification and user stories; there is no indication that the required directories (`src/`, `tests/`, `data/`) have been created or contain any files. The implementer must add the project skeleton with those three top‑level folders (and optionally placeholder files) to satisfy task T001.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T005** — declared artifact(s) missing/empty/invalid: src/data/download_meg.py, data/raw/meg_streamed.parquet
- **T006** — declared artifact(s) missing/empty/invalid: src/data/download_clutrr.py, data/raw/clutrr.parquet, tests/contract/test_clutrr_schema.py
- **T007** — The required output file `data/processed/meg_filtered.npy` is absent, and the provided `src/data/preprocess_meg.py` contains code for Welch PSD computation (Part 2) rather than a band‑pass filter implementation for 30‑50 Hz. Consequently the deliverable and core functionality are missing.
- **T047** — The required output file `data/processed/meg_psd_normalized.npy` does not exist, and the provided `src/data/preprocess_meg.py` is truncated and does not contain a complete implementation (e.g., missing zero‑padding, PSD computation, and normalization logic). Additionally, the referenced `contracts/dataset.schema.yaml` is missing, so verification cannot be performed.
- **T009** — declared artifact(s) missing/empty/invalid: src/models/base_model.py
- **T012** — declared artifact(s) missing/empty/invalid: src/analysis/spectral.py, tests/unit/test_spectral.py
- **T013** — The `src/analysis/sdc.py` file is incomplete and contains a syntax error (unterminated string in the `compute_sdc_batch` function) and is truncated, so the required SDC calculation is not fully implemented. Additionally, the required `contracts/output.schema.yaml` (or `schema.yaml`) file is missing, so the output cannot be verified against the schema.
- **T013b** — declared artifact(s) missing/empty/invalid: src/analysis/plv.py, tests/unit/test_plv.py
