# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The required output file `data/processed/graph_metrics.csv` is missing, so the script has not produced the mandated CSV. Additionally, the provided snippet does not show the required try/except loop with `sys.exit(1)` or explicit peak‑RAM monitoring, indicating the implementation likely does not fully meet the task specifications. The next implementer must ensure the script writes the CSV with the correct schema and includes the prescribed error‑handling and RAM‑monitoring behavior.
- `T041` (rejected 1x): No test file containing `test_collinearity_filter` is present, and there is no evidence of a failing unit test that generates a matrix with duplicate columns and asserts the collinearity filter removes one. The required artifact is missing, so the task is not satisfied.
- `T023` (rejected 1x): The repository contains `code/04_train_model.py`, but the required output artifacts (`data/processed/model.pkl`, `data/processed/cv_results.json`, `data/processed/model_params.json`) are absent, and the provided snippet does not show the required `train_model(data, decline_threshold=3)` callable. These missing files mean the task’s deliverables are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

