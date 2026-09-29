# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018c` (rejected 1x): The required `data/logs/linkage_validation.json` file does not exist, and the provided `constants.py` excerpt does not show the `buffer_size_km` or `grid_resolution_km` definitions needed to generate the mandatory sentence. Consequently, the documentation and JSON artifacts cannot contain the required geospatial fuzzing parameters.
- `T017d` (rejected 1x): declared artifact(s) missing/empty/invalid: data/logs/linkage_validation.json, data/processed/analysis_dataset_village_aggregated.csv, data/processed/analysis_dataset.csv, data/processed/feature_engineered_data.csv
- `T022` (rejected 1x): The required artifact `data/processed/analysis_dataset.csv` does not exist, so the validation script cannot be executed and no assertion of passing validation can be made. The missing dataset must be provided (and be non‑empty) for the task to be completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

