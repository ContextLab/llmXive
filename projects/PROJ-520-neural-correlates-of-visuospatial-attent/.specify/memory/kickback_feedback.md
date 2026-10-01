# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005c` (rejected 1x): No evidence of a `verify_dataset.py` script run, its output, or any log confirming that T005a and T005b logic succeeded and the hard‑gate condition was satisfied. The required artifact (execution result showing the gate passed) is missing.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/metadata.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

