# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T059` (rejected 1x): No code, diff, test output, or documentation was provided to demonstrate that T015a was modified to read from the filtered dataset (threads with ≥3 seed posts) instead of the raw dataset. Evidence such as the updated script, a commit hash, or a test confirming that threads excluded by T010 are no longer processed is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

