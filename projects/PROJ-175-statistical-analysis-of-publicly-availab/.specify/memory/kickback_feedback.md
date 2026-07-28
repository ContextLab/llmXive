# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The required `data/processed/normalized_ingredients.parquet` file is absent, and the existing `data/normalization_report.json` contains placeholder values (`normalized_count: 0`, `status: "NO_DATA"`), indicating that no real normalization was performed. The script also lacks execution logic to generate the parquet output and proper reporting.
- `T015` (rejected 1x): The required output files `data/processed/co_occurrence_matrix.parquet` and `data/matrix_stats.json` are absent, so the co‑occurrence matrix and its verification log were not produced. Consequently the task’s deliverables are not satisfied.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/ingredient_embeddings.parquet, data/processed/similarity_scores.parquet
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/ingredient_roles_residuals.parquet
- `T040b` (rejected 1x): The required output file `data/final/logistic_results_refit.json` is missing, so the logistic regression refit result was not produced as specified. No evidence of the conditional logic or model refitting is present.
- `T025` (rejected 1x): The required output file `data/final/bayesian_results.json` is missing, so the core artifact of the task was not produced. The convergence log exists, but without the results JSON the task’s primary requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

