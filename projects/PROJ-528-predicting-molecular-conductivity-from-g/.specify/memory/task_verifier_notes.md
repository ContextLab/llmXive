# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019b** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv
- **T033a** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T033b** — The required artifact `data/processed/model_results.json` does not exist, so the final R²/MAE values cannot be verified. The task is therefore not completed.
- **T040** — The repository lacks `data/processed/feature_importance.csv` (the file is missing) and the provided `code/analysis.py` excerpt does not contain any implementation of `sklearn.inspection.permutation_importance` or logic to save a ranked feature‑importance list. Consequently the required computation and output were not produced.
- **T045** — declared artifact(s) missing/empty/invalid: data/processed/analysis_summary.json
- **T043** — The repository contains a partially‑implemented `code/plotting.py` (the file ends abruptly and never calls `seaborn.regplot` nor writes a PNG), and the required output file `data/processed/corr_plot_top5.png` is absent. Consequently the task of generating and saving the specified scatter plots was not fulfilled.
- **T049** — The required sample dataset `data/raw/sample_smiles.csv` is missing, and there is no evidence of a `state/validation_log.json` or any execution-time measurement, so the integration test cannot have been performed.
- **T050** — The required data files (`data/processed/descriptors.csv`, `model_results.json`, `analysis_summary.json`) and the descriptor schema (`contracts/descriptor_schema.yaml`) are absent, and there is no evidence of a validation script being run or its results. The task cannot be considered fulfilled.
