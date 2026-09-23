# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T027` (rejected 1x): The repository lacks a `generate_shap_heatmap` implementation in `code/analysis/explainability.py` (the shown code ends with `save_interaction_summary` and is truncated, with no heatmap function). Moreover, the required output file `data/derived/shap_interactions.png` does not exist. Both the function and the expected artifact are missing.
- `T031` (rejected 1x): The required `data/raw/dataset_metadata.json` file does not exist, and the provided `code/data/download.py` snippet (truncated) shows no evidence of the requested metadata generation, schema checks, or status fields. Without the JSON artifact, the task’s core requirement is unmet.
- `T020` (rejected 1x): The repository contains `code/models/random_forest.py`, but the shown excerpt is truncated and does not demonstrate a complete `train_rf` implementation with nested CV, hyperparameter grid, seed handling, or final model saving. Moreover, the required artifact `data/derived/final_model.pkl` is absent. Both the functional output and the expected model file are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

