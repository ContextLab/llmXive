# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The repository lacks the required `data/processed/load_model.pkl` file, and the provided `code/train_load_model.py` is truncated and does not show LightGBM training with `tree_method='hist'`/`device='cpu'`, reading `validation_source.txt`, computing Pearson r, or the conditional save/raise logic. These essential steps and the saved model artifact are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

