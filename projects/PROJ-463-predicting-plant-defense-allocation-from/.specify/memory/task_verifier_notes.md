# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011a** — The repository contains `src/data/verify_metadata.py`, but the file is truncated and there is no `data/processed/metadata_verification_report.json` generated (the file is missing). Without the required output report (and with an incomplete script), the task’s specification is not satisfied.
- **T013** — The provided `src/data/batch_correction.py` does not write the required `data/manifests/batch_correction_report.json` (the file is missing) and lacks a proper ComBat‑seq implementation, does not use `scipy.stats` for the GeNorm M‑value, and does not compute and record the pre‑ and post‑correction CV reduction as specified. The task therefore remains unfinished.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/post_qc_species_list.json
- **T025a** — declared artifact(s) missing/empty/invalid: src/data/traits_try.py, data/processed/post_qc_species_list.json, data/processed/trait_fallback_summary.json
- **T025b** — declared artifact(s) missing/empty/invalid: src/data/traits_fallback.py, data/processed/post_qc_species_list.json, data/processed/trait_fallback_summary.json
- **T025c** — declared artifact(s) missing/empty/invalid: src/data/traits_cache.py
- **T039** — The provided `src/analysis/defense_index.py` is truncated (ends abruptly inside a loop) and does not contain the full logic to compute and write the DAI values. Moreover, the required output file `data/processed/defense_allocation_index.csv` is absent. The task’s core requirements are therefore not satisfied.
- **T040** — declared artifact(s) missing/empty/invalid: src/analysis/reproducibility.py
- **T019a** — declared artifact(s) missing/empty/invalid: src/analysis/feature_engineering.py
