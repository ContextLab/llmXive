# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012#1` (rejected 1x): The `stats.py` file defines the calculation and a `save_power_analysis` function, but it never invokes them, and the required `data/analysis/power_report.json` does not exist. Moreover, the JSON payload includes extra keys (`groups`, `notes`) that are not part of the specified schema. The task’s output file and exact schema are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

