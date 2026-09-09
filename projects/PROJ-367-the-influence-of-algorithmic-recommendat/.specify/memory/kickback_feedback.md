# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): No code, script, or log output was provided that demonstrates added error handling for missing data or a count of excluded sessions. Without any artifact showing the implementation (e.g., updated preprocessing script with try/except blocks and logging statements), the requirement cannot be verified as met.
- `T023` (rejected 1x): No code, script, or documentation implementing the required fallback to Generalized Least Squares with robust standard errors is present; the only artifacts shown relate to data ingestion and PSW, not to the GLS fallback logic. Consequently, the task’s core requirement is unfulfilled.
- `T024` (rejected 1x): No code, script, or log output was provided that implements the required logic to detect extreme propensity‑score weights and to flag methodological changes in the logs, so the claimed feature cannot be verified. The necessary artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

