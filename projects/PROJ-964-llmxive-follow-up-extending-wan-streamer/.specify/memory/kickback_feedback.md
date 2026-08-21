# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014b` (rejected 1x): The repository lacks the required `stratified_sample(df, size)` implementation in `code/data/preprocess.py` (the file ends before such a function is defined) and the expected output file `data/processed/sampled_dataset.parquet` is not present. Both the core function and its resulting artifact are missing, so the task is not satisfied.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/metrics/power_analysis_final.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

