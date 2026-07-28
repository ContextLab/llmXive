# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The required `data/processed/normalized_ingredients.parquet` file is absent, and the existing `data/normalization_report.json` contains placeholder values (`normalized_count: 0`, `status: "NO_DATA"`), indicating that no real normalization was performed. The script also lacks execution logic to generate the parquet output and proper reporting.
- **T015** — The required output files `data/processed/co_occurrence_matrix.parquet` and `data/matrix_stats.json` are absent, so the co‑occurrence matrix and its verification log were not produced. Consequently the task’s deliverables are not satisfied.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/ingredient_embeddings.parquet, data/processed/similarity_scores.parquet
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/ingredient_roles_residuals.parquet
- **T040b** — The required output file `data/final/logistic_results_refit.json` is missing, so the logistic regression refit result was not produced as specified. No evidence of the conditional logic or model refitting is present.
- **T025** — The required output file `data/final/bayesian_results.json` is missing, so the core artifact of the task was not produced. The convergence log exists, but without the results JSON the task’s primary requirement is unmet.
- **T043a** — declared artifact(s) missing/empty/invalid: data/pipeline_execution_log.json
