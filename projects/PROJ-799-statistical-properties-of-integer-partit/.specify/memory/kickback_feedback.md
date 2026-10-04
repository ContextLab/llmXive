# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016b` (rejected 1x): The required `data/processed/features.csv` file is missing, so the validation tests cannot run on real data. Moreover, the test suite does not contain a function named `test_features_non_null` as the task explicitly requests; it only provides separate column‑specific checks. Both the missing CSV and the absent correctly‑named test mean the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

