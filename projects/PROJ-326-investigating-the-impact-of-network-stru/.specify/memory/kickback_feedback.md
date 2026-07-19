# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T035b` (rejected 1x): The required output file `data/analysis/sensitivity_sweep.json` is missing, and the provided unit tests do not include a test named `test_sensitivity_sweep_thresholds` nor do they verify a sweep with ≥5 distinct thresholds as required by SC‑005. The implementation also appears incomplete (truncated functions, no clear `run_sensitivity_sweep` saving logic). These gaps must be addressed for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

