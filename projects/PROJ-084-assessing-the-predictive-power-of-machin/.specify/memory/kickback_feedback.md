# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T026` (rejected 1x): declared artifact(s) missing/empty/invalid: code/modeling/evaluate.py
- `T028` (rejected 1x): No files or directories were presented at `data/results/best_models/`, and there is no code or logs showing that the best model objects and their hyperparameter configurations are being saved there. The required artifact (saved model files and hyperparameter records) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

