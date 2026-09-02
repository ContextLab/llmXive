# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014a** — declared artifact(s) missing/empty/invalid: data/processed/heterogeneity_report.json
- **T014b** — The required input `data/processed/heterogeneity_report.json` does not exist, so the label‑harmonization step cannot be performed as specified. The missing artifact must be provided (or generated) for the task to be considered complete.
- **T017a** — The required input `data/processed/harmonized_labels.csv` is missing, so the pre‑check would raise `DataUnavailableError` and the script was never executed. Consequently the expected output files (`batch_corrected_matrix.csv`, `labels.csv`, `preprocess_log.json`) are also absent. The task therefore is not genuinely completed.
- **T020a** — declared artifact(s) missing/empty/invalid: data/processed/batch_corrected_matrix.csv, data/processed/labels.csv
- **T020c** — No code, notebook, script, or output file that extracts the Random Forest’s feature importances and ranks metabolites by mean decrease in impurity is present. The task required a concrete artifact (e.g., a CSV or figure) showing the importance values and the ordered list of metabolites, which is missing, so the requirement is not met.
- **T021b** — No code, data, or result artifacts (e.g., model training scripts, validation metrics, permutation test outputs, or figures) are present to demonstrate that model validation and permutation testing were performed. The claim lacks any tangible evidence that the required validation pipeline was implemented or executed.
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/batch_corrected_matrix.csv, results/vif_scores.json
- **T024** — declared artifact(s) missing/empty/invalid: results/feature_importance_ranking.json, results/correlation_analysis_raw.json, results/model_validation.json, results/sensitivity_analysis.json, results/vif_scores.json, results/shap_analysis.json
