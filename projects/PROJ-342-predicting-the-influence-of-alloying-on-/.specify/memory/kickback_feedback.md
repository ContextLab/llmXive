# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T024a` (rejected 1x): declared artifact(s) missing/empty/invalid: models/best_model.pkl
- `T024b` (rejected 1x): No `artifacts/metrics/metrics.json` file was presented, and there is no evidence that it contains the required keys (`R2`, `MAE`, `feature_importances`, `null_model_r2`). The implementer must provide the actual JSON file with those entries.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

