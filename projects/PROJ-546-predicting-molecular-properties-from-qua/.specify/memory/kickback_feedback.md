# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): No code, configuration, log files, or documentation showing that logging for DFTB+ invocation, timing, and resource usage has been added is present. The implementer provided only the task description and specifications, but no concrete artifact (e.g., Python module, logging config, example log output) that fulfills the requirement. The missing implementation must be supplied for the task to be considered complete.
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/evaluation.json
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/evaluation.json
- `T025` (rejected 1x): declared artifact(s) missing/empty/invalid: data/performance_metrics.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

