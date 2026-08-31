# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): The repository lacks the required `data/processed/split_indices.json` file, and the provided `code/modeling.py` does not contain any implemented logic that performs an 80/20 `train_test_split` and writes the indices to that JSON (the file is truncated and no such function is present). Consequently the task’s output and verification steps are not satisfied.
- `T021` (rejected 1x): The required `data/processed/alloys_clean.parquet` file is absent, and the expected output `results/cv_best_hyperparameters.json` does not exist. Moreover, the provided `code/modeling.py` is truncated and does not contain a concrete implementation of repeated 5‑fold cross‑validation that uses only the training indices, nor does it write the best hyperparameters to the specified JSON file. These critical artifacts are missing, so the task is not genuinely completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

