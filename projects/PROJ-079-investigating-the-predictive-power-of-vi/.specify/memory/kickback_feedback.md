# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/isg_scores.csv
- `T017` (rejected 1x): The required file `src/preprocess.py` does not exist, so the `filter_samples` function cannot be present or verified. Consequently the task’s implementation is missing.
- `T018b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/features.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

