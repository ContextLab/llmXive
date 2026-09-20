# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T022b** — The repository contains the verification script, but the required `data/processed/features.csv` (and consequently the log file) is missing, so the script cannot actually confirm the presence of the required columns. The task’s core requirement—to assert that the CSV exists and includes the specified columns—is not met.
- **T027a** — The `StabilitySelection` class in `code/classification/models.py` is only partially shown and ends abruptly (the loop body is incomplete, no feature‑selection logic, and no code to write `stable_features.csv`). Moreover, the required output file `data/processed/stable_features.csv` does not exist. Both the algorithm implementation and the required saved results are missing.
- **T031** — declared artifact(s) missing/empty/invalid: data/metadata/analysis_config.json, data/processed/features.csv, data/processed/features_sim_med.csv
- **T031b** — declared artifact(s) missing/empty/invalid: data/processed/features_sim_med.csv, data/processed/sensitivity_results.json
