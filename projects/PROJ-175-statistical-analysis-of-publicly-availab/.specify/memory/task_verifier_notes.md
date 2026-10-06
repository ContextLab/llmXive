# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013a** — declared artifact(s) missing/empty/invalid: data/raw/recipe1m_processed.parquet, data/logs/recipe1m_validation.json
- **T014a** — No code, data file, or mapping artifact for ingredient name normalization and canonical ID mapping was provided. The task required a concrete implementation (e.g., a script or dataset) that normalizes raw ingredient strings and produces a canonical ID mapping, but the evidence contains only a placeholder comment and no tangible output.
- **T014b** — declared artifact(s) missing/empty/invalid: data/processed/functional_roles.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/co_occurrence_matrix.parquet
- **T016b** — The required output file `data/processed/similarity_scores_embedding.parquet` does not exist, and there is no evidence that the embedding model was run on the normalized ingredients CSV. The task therefore was not completed.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/functional_roles_validated.parquet
- **T019a** — No code, data files, CSV output, model fitting results, or figures were supplied; the claim contains only the specification text without any tangible artifacts to verify that the data pipeline or statistical models were actually built and executed. The required deliverables (e.g., a validated CSV of ingredient pairs, model coefficient plots, test statistics) are missing.
- **T019b** — No concrete artifacts (e.g., preprocessing scripts, generated CSV with ingredient pair statistics, model fitting code, coefficient plots, or validation reports) were supplied. Without these files or outputs, the required data pipeline and statistical modeling steps cannot be verified as completed. The implementer must provide the actual code, generated dataset, and model evaluation artifacts to satisfy the task.
- **T023** — declared artifact(s) missing/empty/invalid: data/logs/vif_scores.json
- **T025** — The required output file `data/logs/bayesian_results.json` is missing, so the hierarchical Bayesian model fitting result was not produced. Without this artifact, the task’s core requirement is not satisfied.
- **T029** — declared artifact(s) missing/empty/invalid: data/logs/evaluation_metrics.csv
- **T030** — declared artifact(s) missing/empty/invalid: docs/calibration_plot.png
