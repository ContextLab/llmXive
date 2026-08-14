# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010b** — The provided `code/02_preprocess_eeg.py` is truncated and does not show the required exclusion‑ratio check, ICA‑success gating, or saving of cleaned `.fif` files and `exclusion_log.csv`. Moreover, the expected `data/interim/exclusion_log.csv` file is absent. The task’s output artifacts are therefore missing or incomplete.
- **T012** — The repository contains a partially‑implemented `code/03_extract_features.py` that stops mid‑function and never writes `data/interim/eeg_psd.csv` (the file is missing). Moreover, the script does not enforce 5‑minute epoch segmentation, nor does it demonstrate the required chunked processing or global‑mean aggregation for all subjects. The essential output artifact is absent, so the task is not fulfilled.
- **T013** — declared artifact(s) missing/empty/invalid: data/interim/behavioral_metrics.csv, data/interim/behavioral_exclusion_log.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/interim/eeg_psd.csv, data/interim/behavioral_metrics.csv, data/processed/features.csv
- **T035a** — The required artifact `data/processed/features.csv` is missing, so no schema validation could be performed; thus the task’s requirements are not met.
- **T017** — The repository contains `code/04_modeling.py`, but the required input `data/processed/features.csv` is absent, and the script has not produced the mandated output files `data/interim/split_indices.json` and `data/processed/model_results.json`. Without these files the modeling step cannot be executed, so the task is not genuinely completed.
- **T019** — The required artifact `data/processed/model_results.json` does not exist, so the adjusted R² and optimal lambda have not been logged as specified. The task therefore remains unfinished.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/features.csv
- **T022a** — declared artifact(s) missing/empty/invalid: data/interim/split_indices.json, data/processed/model_results.json, data/interim/permutation_null_distribution.npy
- **T022b** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/correlations.csv, data/processed/non_linear_comparison.json
- **T035b** — Both required artifacts (`data/processed/model_results.json` and `data/processed/correlations.csv`) are missing from the repository, so no schema validation could have been performed. The task’s core deliverable is absent.
- **T026c** — The required output files `data/interim/robustness/no_ica/features.csv` and `data/interim/robustness/window_2s/features.csv` are absent, and the provided `code/05_robustness_features.py` excerpt does not show any code that writes these CSVs. Thus the robustness feature extraction and CLR processing have not been completed and the task’s deliverables are missing.
