# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — The `baseline_test_predictions.csv` on disk is a fabricated placeholder: `predicted_value` equals `experimental_value` for every row (perfect predictions), and solubility/boiling_point values are all 0.0 — exactly matching the `_generate_baseline_test_predictions()` fallback in `stats.py`, which fabricates "perfect baseline prediction" data. Consequently `baseline_metrics.csv` reports MAE=RMSE=0.0 for all three properties, which is not a genuine baseline measurement (FR-005 baseline side). The code, CSV, PNG, and test exist and match the schema, but the underlying predictions are synthetic sta
- **T102** — Requested task execution failed; rerun successfully: code/analysis/explainability.py exit=1
