# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T023` (rejected 1x): No code, notebook, or output implementing a post‑hoc power analysis with `statsmodels` is present; the evidence lacks any artifact that performs or reports such an analysis. The required deliverable is missing.
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/correlations_corrected.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

