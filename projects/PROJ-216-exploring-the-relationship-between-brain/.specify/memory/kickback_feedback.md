# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/resource_profile.json
- `T017d` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/preprocessing_stats.json
- `T018b` (rejected 1x): No `preprocess.py` file or code changes were presented, and there is no evidence of logging excluded subjects while retaining their raw data. The required logic to “handle subjects after motion exclusion, ensuring excluded subjects are logged but not removed” is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

