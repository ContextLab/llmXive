# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T023d` (rejected 1x): declared artifact(s) missing/empty/invalid: results/model_metrics.json, schema.yaml
- `T030a` (rejected 1x): The required input files (`results/model_metrics.json`, `results/collinearity_diagnostic.json`, `results/feature_importance_summary.json`, `results/methodological_flags.json`, `models/rf_model.pkl`, `results/residuals.json`) are all missing, and no `results/final_report.md` was produced. Moreover, the shown `code/main.py` is truncated and does not contain the logic to write the markdown report, so the verification criteria cannot be satisfied.
- `T023c` (rejected 1x): The repository lacks the required `results/methodological_flags.json` file, and the provided `code/modeling.py` excerpt does not show any logic that computes cross‑validation MAE, compares it to 0.05, sets `mae_flag`, and writes the JSON file. The implementation of the MAE calculation and logging is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

