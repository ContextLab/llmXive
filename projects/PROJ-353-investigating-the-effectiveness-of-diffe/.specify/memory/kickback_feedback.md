# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): No updated `spec.md` file is provided, and there is no evidence showing that the text of FR‑005 and US‑2 Acceptance Scenario 1 has been edited to replace “≥ [deferred]” with “≥ 0.90”. The implementer’s claim cannot be verified without the actual specification document.
- `T013` (rejected 1x): No `spec.md` file or excerpt showing the required changes is provided; therefore we cannot confirm that FR‑006 and FR‑007 have been updated to replace “Pearson correlation” and “ANCOVA” with “Tobit Regression” and “Cox Proportional Hazards”. The implementer must supply the modified `spec.md` containing the corrected functional requirement text.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

