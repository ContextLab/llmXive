# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T031b` (rejected 1x): No execution logs, result files, or gating evidence for the Synthetic Ground Truth test (T031a) are present; the implementer did not provide any artifact showing the recovery rate calculation or a decision that blocks subsequent phases. Consequently, the requirement to run the test and enforce the 5 % recovery‑rate gate is not demonstrated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

