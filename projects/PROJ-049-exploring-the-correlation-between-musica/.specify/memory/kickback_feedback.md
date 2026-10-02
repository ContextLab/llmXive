# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000a` (rejected 1x): The `results/power_analysis.txt` file is absent, and the state YAML still has `required_sample_size: null`, indicating the script never wrote or parsed the sample size nor updated `research.md`. The implementation is incomplete and does not satisfy the task’s output and update requirements.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

