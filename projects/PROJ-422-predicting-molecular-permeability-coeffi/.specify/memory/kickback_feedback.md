# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): Checked `code/data/split.py`, `data/processed/processed_data.parquet`, and the generated `data/processed/train.parquet`/`test.parquet`. The script falls back to a random split (with warning) because `polymer_type` is absent, but the dataset contains only one row, so it puts everything in the train set and leaves the test set empty. No `train.csv`/`test.csv` files are present in the evidence, and the split ratio is not the required ≈ 0.8/0.2, violating the test’s expected checks.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

