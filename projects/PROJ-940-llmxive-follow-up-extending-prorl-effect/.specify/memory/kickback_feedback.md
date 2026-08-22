# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T025` (rejected 1x): The provided `src/main.py` does not contain any logic that computes the mean absolute difference between rectified and raw scores or writes a `results/sc005_status.json` file, and the required `results/sc005_status.json` file is absent from the repository. Both the validation implementation and the output artifact are missing.
- `T028b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/stats.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

