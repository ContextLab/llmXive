# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The required `data/processed/metrics.csv` file does not exist, so no thermal conductivity scalar could be appended, and the assertion/logging behavior cannot be verified. The only log present (`results/power_analysis.log`) records a pipeline failure due to the missing metrics file, not the expected discrepancy logging. The task therefore fails to meet its core requirements.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

