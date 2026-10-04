# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019a** — declared artifact(s) missing/empty/invalid: data/processed/descriptors_base.csv
- **T019b** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv
- **T032c** — The required artifact `data/processed/model_results.json` does not exist, so the sensitivity analysis results have not been recorded as the task demands. The implementer must create this file and populate it with the appropriate sensitivity analysis data.
- **T033a** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T033b** — The required artifact `data/processed/model_results.json` does not exist, so the final R²/MAE values cannot be verified. The task is therefore not completed.
- **T039d** — The required artifact `data/processed/model_results.json` does not exist, so no data (including final R²/MAE) can be verified against the schema. The task cannot be considered completed until this JSON file is created, populated with the appropriate fields, and conforms to `contracts/model_results_schema.yaml`.
- **T040** — The repository lacks the required `data/processed/feature_importance.csv` file, and the provided `code/analysis.py` does not contain any implementation of `sklearn.inspection.permutation_importance` nor code that writes a ranked feature‑importance list to that CSV. The task’s core output is therefore missing.
- **T045** — declared artifact(s) missing/empty/invalid: data/processed/analysis_summary.json
