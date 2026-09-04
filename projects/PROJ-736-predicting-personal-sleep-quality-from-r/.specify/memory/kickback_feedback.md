# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): The provided `code/modeling/train.py` is incomplete (truncated mid‑function and does not show a call to T020a or saving of a model). Moreover, the required output files `data/processed/predictions.npy` and `data/processed/model.pkl` are absent from the repository. The task’s core deliverables are therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

