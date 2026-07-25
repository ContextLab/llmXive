# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided evidence contains only a feature specification and user stories; there is no indication that the required directories (`src/`, `tests/`, `data/`) have been created or contain any files. The implementer must add the project skeleton with those three top‑level folders (and optionally placeholder files) to satisfy task T001.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T005** — declared artifact(s) missing/empty/invalid: src/data/download_meg.py, data/raw/meg_streamed.parquet
- **T006** — declared artifact(s) missing/empty/invalid: src/data/download_clutrr.py, data/raw/clutrr.parquet, tests/contract/test_clutrr_schema.py
- **T007** — declared artifact(s) missing/empty/invalid: src/data/preprocess_meg.py, data/processed/meg_filtered.npy
- **T047** — declared artifact(s) missing/empty/invalid: src/data/preprocess_meg.py, data/processed/meg_psd_normalized.npy, schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: src/data/preprocess_meg.py
- **T009** — declared artifact(s) missing/empty/invalid: src/models/base_model.py
- **T012** — declared artifact(s) missing/empty/invalid: src/analysis/spectral.py, tests/unit/test_spectral.py
- **T013** — The `src/analysis/sdc.py` file is incomplete and contains a syntax error (unterminated string in the `compute_sdc_batch` function) and is truncated, so the required SDC calculation is not fully implemented. Additionally, the required `contracts/output.schema.yaml` (or `schema.yaml`) file is missing, so the output cannot be verified against the schema.
- **T013b** — declared artifact(s) missing/empty/invalid: src/analysis/plv.py, tests/unit/test_plv.py
- **T017** — declared artifact(s) missing/empty/invalid: src/models/oscillatory_attention.py
- **T018** — declared artifact(s) missing/empty/invalid: src/main.py
- **T018b** — declared artifact(s) missing/empty/invalid: src/main.py
- **T021** — declared artifact(s) missing/empty/invalid: data/final/control_run_comparison.json
- **T020** — The submission provides no code, notebook, data file, or result output that computes the peak power in the 38‑42 Hz band, compares it to adjacent bands, or asserts that the SNR meets the ≥ 3 dB threshold using T021 control data. Without any tangible artifact (e.g., a script, log, or figure) the requirement is not satisfied. The next implementer must deliver a concrete implementation and evidence (e.g., a Python script/notebook and its execution output) showing the SNR calculation and verification.
