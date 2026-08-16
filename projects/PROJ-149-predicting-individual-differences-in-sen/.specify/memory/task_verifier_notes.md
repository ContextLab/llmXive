# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010a** — The required `data/interim/exclusion_log.csv` file is missing, and there is no evidence that the script produced the `data/interim/cleaned_eeg_final/` directory with `.fif` files. Without these output artifacts, the task’s mandatory deliverables are not satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: data/interim/behavioral_metrics.csv, data/interim/behavioral_exclusion_log.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/interim/eeg_psd.csv, data/interim/behavioral_metrics.csv, data/processed/features.csv
- **T035a** — The required artifact `data/processed/features.csv` does not exist, so no schema validation can be performed. The task’s core requirement (checking columns, nulls, and RT range) cannot be satisfied without the file.
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T026c** — The required output files `data/interim/robustness/no_ica/features.csv` and `data/interim/robustness/window_2s/features.csv` are not present, indicating the script either was not executed or does not generate the expected CSVs. Consequently the task’s core deliverable is missing.
- **T026d** — The required input CSVs (`data/interim/robustness/no_ica/features.csv` and `data/interim/robustness/window_2s/features.csv`) are absent, and the expected output `data/interim/robustness/robustness_report.csv` was not generated. Moreover, the provided `code/05_robustness_modeling.py` is truncated and does not contain the logic to load both feature sets, compute the alpha‑power percentage difference, or write the robustness report. These missing artifacts prevent the task from being fulfilled.
