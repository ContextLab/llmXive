# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — declared artifact(s) missing/empty/invalid: data/processed/final_dataset.parquet
- **T017** — The required dataset `data/processed/final_dataset.parquet` does not exist, so the training script cannot actually load the crystallization labels. Moreover, the provided portion of `code/models/train.py` is truncated before any classifier training or confusion‑matrix‑saving logic, so it’s unclear whether those steps are implemented. Both the essential input file and the explicit saving of the confusion matrix are missing.
