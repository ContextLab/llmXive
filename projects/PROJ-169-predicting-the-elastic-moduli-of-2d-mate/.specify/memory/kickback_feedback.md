# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018b` (rejected 1x): The provided `code/model/train.py` exists, but the required output artifacts (`data/processed/model_v1.pt` and a `predictions.json` for the test set) are missing, and the script does not demonstrably enforce CPU‑only execution, use `tracemalloc` to record peak memory, or guarantee the T046 disclaimer is emitted. Consequently the task’s core requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

