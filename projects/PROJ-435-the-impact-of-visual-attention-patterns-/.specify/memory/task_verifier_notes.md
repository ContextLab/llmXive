# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004b** — The required input file `data/raw/eye_tracking_raw.parquet` does not exist, and the expected output `data/derived/empirical_outcomes.csv` is also missing, so the extraction and writing steps cannot have been performed. The task’s core artifact is absent.
- **T021** — declared artifact(s) missing/empty/invalid: data/derived/empirical_outcomes.csv, data/derived/valence_scores.csv
- **T018** — The repository contains a `code/02_preprocess_gaze.py` file, but it is truncated and does not show the full implementation of data‑loss filtering, ROI mapping, or edge‑case handling, and the required output `data/derived/preprocessed_gaze.csv` (and the exclusion log) are absent. Without these artifacts the task’s deliverables are not satisfied.
- **T040** — The required input `data/derived/preprocessed_gaze.csv` does not exist, so the script cannot compute the report, and no `output/data_quality_report.csv` is present. Additionally, the provided `code/02_data_quality_report.py` is truncated and does not show the final logic that writes the CSV. The task’s core output is therefore missing.
