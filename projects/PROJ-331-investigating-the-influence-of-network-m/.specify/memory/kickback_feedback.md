# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The provided `code/utils.py` is truncated and does not contain any logic that validates the presence of Bonferroni alpha, seed, library versions, permutation count, or VIF threshold in the log, nor does it ensure that all processing steps, warnings, and errors are captured. Additionally, the required `data/logs/pipeline.log` file is absent. These missing pieces prevent the task from being fully satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

