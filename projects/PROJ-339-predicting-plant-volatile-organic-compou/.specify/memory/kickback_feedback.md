# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No code, configuration files, or documentation were provided to show that environment variables for data paths and random seeds have been set up or managed. The claim lacks any tangible artifact demonstrating the required configuration.
- `T016` (rejected 1x): No code, script, notebook, or data artifact showing that gene‑expression values were aggregated into pathway‑level (e.g., TPS family) features is present. The claim lacks any tangible implementation or output that demonstrates the required dimensionality‑reduction step.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/merged_dataset.csv, data/results/data_validation_report.json
- `T022` (rejected 1x): No code, notebook, or configuration file is present that demonstrates imputation parameters being fitted exclusively on training folds; the claim is unsupported by any artifact. A concrete implementation (e.g., a preprocessing pipeline integrated with cross‑validation that fits the imputer inside each training split) is required to satisfy T022.
- `T023` (rejected 1x): The required artifact `data/results/model_metrics.json` does not exist, so no R² or RMSE metrics are provided. The implementer must create this JSON file with the calculated metrics.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/models/random_forest.pkl
- `T025` (rejected 1x): The required artifacts `data/results/model_metrics.json` and `data/results/interpretation_report.json` do not exist on disk, so the disclaimer cannot be present and the tests in `tests/test_model.py` would fail. The implementer must create these JSON files with the appropriate keys (`disclaimer` containing “associational” and “observational”) and the other required metric fields.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

