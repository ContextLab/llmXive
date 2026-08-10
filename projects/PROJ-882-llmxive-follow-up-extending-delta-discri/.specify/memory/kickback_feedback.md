# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/static_features.parquet, schema.yaml
- `T022` (rejected 1x): The `code/models/train.py` script exists, but the required output model file `data/processed/mlp_model.pt` is missing, so the implementation does not fulfill the task’s requirement to save the trained model.
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/predictions.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

