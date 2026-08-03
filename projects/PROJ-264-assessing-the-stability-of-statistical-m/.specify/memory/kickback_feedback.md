# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T013` (rejected 1x): No code, data files, or output artifacts (e.g., the cross‑validation loop, metric logs, or summary tables) were presented. Without any tangible implementation or results, we cannot confirm that accuracy and F1 are calculated inside the CV loop or that leakage is prevented. The required artifacts are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

