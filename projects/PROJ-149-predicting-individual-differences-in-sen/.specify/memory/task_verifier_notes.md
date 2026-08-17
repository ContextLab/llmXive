# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The provided `code/03_extract_features.py` is truncated (e.g., undefined `pid` variable) and raises a `FileNotFoundError` when `exclusion_log.csv` is absent, contrary to the requirement to handle a missing/empty exclusion log gracefully. Moreover, the required output file `data/interim/eeg_psd.csv` does not exist, and the exclusion log itself is missing. The script therefore does not fulfill the task’s specifications.
- **T013** — declared artifact(s) missing/empty/invalid: data/interim/behavioral_metrics.csv, data/interim/behavioral_exclusion_log.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/interim/eeg_psd.csv, data/interim/behavioral_metrics.csv, data/processed/features_clr.csv
- **T035a** — The required artifact `data/processed/features_clr.csv` does not exist, so no schema validation (null checks, column verification, RT range check) could be performed. The task cannot be considered completed until the CSV file is present and validated as specified.
- **T017** — The repository contains `code/04_modeling.py`, but the required input `data/processed/features_clr.csv` is absent, and the script never produced the declared outputs `data/interim/split_indices.json` and `data/processed/model_results.json`. Without these files the modeling step cannot be executed, so the task’s requirements are not met.
- **T019** — The required output file `data/processed/model_results.json` is missing, so no Adjusted R² or optimal lambda values have been logged. The task’s primary artifact does not exist, indicating the work is not done.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/features_clr.csv
- **T022a** — declared artifact(s) missing/empty/invalid: data/interim/split_indices.json, data/processed/model_results.json, data/interim/permutation_null_distribution.npy
