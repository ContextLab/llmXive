# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T022` (rejected 1x): No code, test, or documentation for the edge‑case handling (fallback to variance‑based metric when spectral density fails) was provided; the claim lacks any tangible artifact to verify that the fallback logic was implemented and integrated. The required implementation is therefore missing.
- `T037b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/regression.py, data/results/filtered_features.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

