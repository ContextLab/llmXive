# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T051` (rejected 1x): The required output file `data/processed/sensitivity_report.csv` does not exist, so the “Unstable” flag cannot be recorded. Additionally, the provided `code/stats.py` excerpt is truncated and does not show any logic that writes such a flag to the CSV. The task’s core deliverable is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

