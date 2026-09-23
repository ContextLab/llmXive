# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013a** — declared artifact(s) missing/empty/invalid: data/processed/pre_imputation_validation.json
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/imputed_data.csv, data/processed/post_imputation_validation.json
- **T016** — The repository contains `preprocess.py`, but the shown code stops before any imputation or file‑write logic and the required output file `data/processed/imputed_data.csv` is absent. Consequently the task’s critical output (saving the imputed DataFrame) is not present. The implementer must add the imputation step (using miceforest or IterativeImputer) and write the resulting DataFrame to the specified CSV path.
- **T016a** — declared artifact(s) missing/empty/invalid: data/processed/imputed_data.csv
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/regression_coefficients.csv, data/processed/model_diagnostics.json
- **T028a** — The required output file `data/processed/sensitivity_sweep_results.csv` does not exist, and the provided `sensitivity.py` only contains utility functions for loading data and computing bias—it lacks any implementation of a p‑value/ imputation‑limit sweep, logging to `logs/sensitivity.log`, or generation of the specified CSV columns. The task’s core functionality is therefore not fulfilled.
