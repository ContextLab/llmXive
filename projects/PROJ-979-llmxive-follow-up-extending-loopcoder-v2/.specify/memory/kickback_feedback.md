# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005e` (rejected 1x): The `capture_metrics()` function in `code/src/utils.py` is incomplete: it never computes or records the elapsed runtime, contains a syntax error (`e`), and does not write the metrics to `data/processed/resource_metrics.json`. Moreover, the required JSON file is missing from the repository.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

