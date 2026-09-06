# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007g** — declared artifact(s) missing/empty/invalid: data/processed/golden_set.csv
- **T007f** — The repository contains no `data/processed/golden_set.csv` and no code that performs the required validation‑and‑halt logic (checking T004 for a public NASA‑TLX dataset and raising the exact error message). Without this implementation the task’s specification is not satisfied. The missing artifact is the pipeline code that enforces the golden‑set existence check and produces the mandated HALT error.
- **T008** — declared artifact(s) missing/empty/invalid: data/processed/golden_set.csv
- **T015** — The repository lacks the required `data/processed/golden_set.csv` and the model/metrics files (`load_model.pkl`, `load_model_low_confidence.pkl`, `model_metrics.json`). Without the Golden Set the training script cannot run, and the expected output artifacts are absent. Additionally, the provided `train_load_model.py` is truncated, so we cannot confirm it implements the full LightGBM pipeline and conditional saving logic. The task is therefore not satisfied.
- **T018** — The required artifact `data/processed/load_model.pkl` does not exist, so the existence check cannot pass and no file size verification can be performed. The task’s condition to raise an error for a missing or oversized model is therefore not satisfied.
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/instructional_units.csv
- **T022b** — declared artifact(s) missing/empty/invalid: data/processed/instructional_units.csv, data/explanation_tiers/moderate_tiers.csv
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/instructional_units.csv, data/explanation_tiers/simple_tiers.csv
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/instructional_units.csv, data/explanation_tiers/complex_tiers.csv
