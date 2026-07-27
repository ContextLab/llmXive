# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The provided `preprocess.py` only defines helper functions; it never runs a normalization pass over the Recipe1M ingredient list, nor does it record mapping or exclusion counts. The `data/normalization_config.json` file is empty, showing no logging occurred. Additionally, the `normalize_ingredient_name` logic does not enforce the ≤ 2 distance threshold correctly. The script needs a processing loop that applies the Levenshtein‑based normalization, respects the distance limit, and writes the required statistics to the JSON file.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/co_occurrence_matrix.parquet
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/flavor_similarity.parquet
- **T040b** — The required artifact `data/final/logistic_results.json` does not exist, so the logistic regression re‑fit after predictor drop has not been recorded as required. The task therefore remains unfinished.
- **T022** — The required output file `data/final/logistic_results.json` is missing, and the predictor list in `data/final_predictors.json` does not contain the specified predictors (frequency, similarity, role) but only placeholder names. Both essential artifacts are absent/incorrect, so the task is not satisfied.
- **T025** — The required output file `data/final/bayesian_results.json` is missing, so the core artifact of the task was not produced. The convergence log exists, but without the results JSON the task’s primary requirement is unmet.
- **T047** — declared artifact(s) missing/empty/invalid: data/vif_test_set.json
- **T029** — declared artifact(s) missing/empty/invalid: data/evaluation_metrics.json
