# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/solubility_features.csv
- `T023` (rejected 1x): The required artifact `data/artifacts/trained_models.pkl` does not exist, and `code/04_evaluation.py` does not compute RMSE, MAE, or R² (it only computes absolute errors and a paired t‑test). Both the data dependency and the specified evaluation metrics are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

