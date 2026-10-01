# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T082` (rejected 1x): No updated `plan.md` file is presented, so we cannot confirm that the “Candidate‑Gene Pre‑filtering” entry was removed from both the “Complexity Tracking” table and the “Critical Methodological Adjustment” section as required. The necessary artifact is missing.
- `T083` (rejected 1x): No updated `plan.md` file was provided; there is no evidence that Phase 3 now explicitly mentions using `StratifiedKFold(n_splits=5)` and an 80/20 train‑test split, nor that the placeholder “[deferred] split” language was removed. The required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

