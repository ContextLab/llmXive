# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The required output file `data/processed/graph_metrics.csv` does not exist, so the primary artifact is missing. Moreover, the script raises a `MemoryError` instead of exiting with `EXIT_CODE_RAM_EXCEEDED = 5`, and it does not appear to track peak RAM usage as specified. The implementation therefore does not meet the task requirements.
- `T041` (rejected 1x): No unit‑test file, test suite, or code snippet was provided that actually verifies the collinearity filter drops one of a pair of features with Pearson > 0.95. The claim lacks any concrete artifact (e.g., a pytest file, test output, or CI log) to confirm the required behavior, so the requirement is not satisfied.
- `T023` (rejected 1x): The provided `code/04_train_model.py` is incomplete/truncated and does not show the required nested‑CV loop, inner‑loop feature‑selection steps, or the saving of `model.pkl`, `cv_results.json`, and `model_params.json`. Moreover, the expected output files are absent from the repository. The task’s core requirements are therefore not demonstrably satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

