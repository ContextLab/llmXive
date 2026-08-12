# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No code, script, configuration, or documentation for a resource‑monitoring wrapper is present; the only artifacts shown relate to data ingestion, modeling, and reporting, not to CPU‑time or RAM enforcement. Consequently the required implementation of a monitoring wrapper that enforces the 6‑hour / 7 GB limits is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

