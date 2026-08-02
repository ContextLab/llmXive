# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): No code, scripts, or logs were provided that perform the required structure validation (BVS deviation <10% and Li‑O distance 1.95–2.15 Å) or that record any violations, as mandated by FR‑002 and Section 3.2. The implementer’s claim lacks the necessary artifact to demonstrate the functionality.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

