# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — declared artifact(s) missing/empty/invalid: data/processed/final_dataset.parquet
- **T015** — The required `data/processed/final_dataset.parquet` file does not exist, so the script cannot actually load the dataset. Moreover, the `split_data_stratified` function stratifies on the target variable (`y`) instead of the chemical family column, which does not meet the task’s specification. Both the missing data file and incorrect stratification need to be fixed.
- **T017** — The `code/models/train.py` file is present but only shows the beginning of a regression implementation; there is no visible code that trains a Random Forest **classifier**, generates a confusion matrix, or saves it. Moreover, the required input file `data/processed/final_dataset.parquet` is missing entirely, so the script cannot even load the crystallization labels. Both the essential dataset and the classifier/confusion‑matrix functionality are absent.
- **T018** — The repository contains a `train.py` file, but it is truncated and does not clearly show a k‑fold cross‑validation implementation, and the required output files `models/tg_regressor.pkl` and `models/crystallization_classifier.pkl` are absent from the project. The task’s core deliverables are therefore missing.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.json, data/processed/final_dataset.parquet
- **T020** — declared artifact(s) missing/empty/invalid: docs/reports/metrics.json
- **T023** — declared artifact(s) missing/empty/invalid: docs/reports/collinearity_report.json, data/processed/final_dataset.parquet
