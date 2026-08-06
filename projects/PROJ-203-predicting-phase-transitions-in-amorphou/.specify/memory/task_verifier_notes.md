# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — declared artifact(s) missing/empty/invalid: data/processed/final_dataset.parquet
- **T015** — The `train.py` file is present but truncated (the shown code ends abruptly and does not include any train/test split logic), and the required dataset file `data/processed/final_dataset.parquet` is missing from the repository. Both the core functionality (stratified split) and the prerequisite data are absent, so the task is not genuinely completed.
- **T017** — The required `data/processed/final_dataset.parquet` file is absent, so the training script cannot load the labels. The expected confusion‑matrix image `docs/reports/confusion_matrix.png` is also missing. Moreover, the provided `code/models/train.py` is truncated and does not show the full Random Forest classifier training or the code that writes the PNG, indicating the implementation is incomplete.
- **T018** — The `train.py` file is present but the provided excerpt ends abruptly and shows no actual k‑fold cross‑validation logic or model‑saving code, and the required model files `models/tg_regressor.pkl` and `models/crystallization_classifier.pkl` are absent from the repository. Both the functional implementation and the saved artifacts are missing.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.json
