# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No code, configuration files, or documentation were provided to show that environment variables for data paths and random seeds have been set up or managed. The claim lacks any tangible artifact demonstrating the required configuration.
- **T016** — No code, script, notebook, or data artifact showing that gene‑expression values were aggregated into pathway‑level (e.g., TPS family) features is present. The claim lacks any tangible implementation or output that demonstrates the required dimensionality‑reduction step.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/merged_dataset.csv, data/results/data_validation_report.json
- **T022** — No code, notebook, or configuration file is present that demonstrates imputation parameters being fitted exclusively on training folds; the claim is unsupported by any artifact. A concrete implementation (e.g., a preprocessing pipeline integrated with cross‑validation that fits the imputer inside each training split) is required to satisfy T022.
- **T023** — The required artifact `data/results/model_metrics.json` does not exist, so no R² or RMSE metrics are provided. The implementer must create this JSON file with the calculated metrics.
- **T024** — declared artifact(s) missing/empty/invalid: data/models/random_forest.pkl
- **T025** — The required artifacts `data/results/model_metrics.json` and `data/results/interpretation_report.json` do not exist on disk, so the disclaimer cannot be present and the tests in `tests/test_model.py` would fail. The implementer must create these JSON files with the appropriate keys (`disclaimer` containing “associational” and “observational”) and the other required metric fields.
- **T031** — No code, script, notebook, or result files were provided that perform the required overlap‑statistics calculation between the aggregated pathway features from T016 and the known terpene synthase gene families (FR‑008). Without such an artifact, the task’s core requirement cannot be verified. The implementer must supply the implementation (e.g., a Python script or notebook) and its output (statistics, tables, or visualizations) showing the overlap analysis.
- **T032** — declared artifact(s) missing/empty/invalid: data/results/interpretation_report.json
- **T033** — declared artifact(s) missing/empty/invalid: data/results/stability_metrics.json
