# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/state.json
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/covariance_matrix.npy
- `T023` (rejected 1x): No code, script, or output file implementing the `emcee` runner was provided; the evidence on disk contains no artifact that starts with 5 000 steps, checks Gelman‑Rubin, and continues in 1 000‑step batches. Consequently the required functionality is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

