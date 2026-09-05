# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002v` (rejected 1x): No actual `constitution.md` file or its Principle VI text was provided, so we cannot confirm that it explicitly permits FFT‑based numerical homogenization nor that it documents the validity range of analytical bounds, nor see the required “[X]” mark. The required artifact is missing.
- `T004v` (rejected 1x): No actual `spec.md` file or excerpt showing the required “128x128 pixels” text was provided, nor any evidence (e.g., a marked checklist or screenshot) that the implementer inspected the document and marked it as completed. The claim lacks the required artifact.
- `T005v` (rejected 1x): No evidence was provided that `spec.md` (FR‑007) and `plan.md` (Methodology) were inspected or that they contain the explicit phrase “One-way ANOVA and Tukey HSD”, nor is there any marked [X] indicating completion. The required artifacts and verification are missing.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

