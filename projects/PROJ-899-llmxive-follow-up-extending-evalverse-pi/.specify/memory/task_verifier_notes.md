# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019** — The `src/models/evaluate.py` only provides MSE‑based baseline functions and a generic CSV writer; it does not compute RMSE or R², does not include the required columns (`dimension`, `predictor_type`, `rmse`, `r2`), and lacks any validation against the best model from T015 or the majority‑dimension check. Moreover, the expected output file `data/baseline_results.csv` is absent. The task’s core requirements are therefore unmet.
- **T017** — declared artifact(s) missing/empty/invalid: src/reports/generate.py
- **T018** — declared artifact(s) missing/empty/invalid: data/dimension_viability.csv
