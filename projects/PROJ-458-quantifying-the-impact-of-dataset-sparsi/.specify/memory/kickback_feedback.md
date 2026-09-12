# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T054` (rejected 1x): No updated `spec.md` file or excerpt is provided showing that FR‑003’s wording was changed from “full dataset (150k)” to “Representative Stratified Sample (RSS) of [deferred] entries” nor that the generic “[deferred] levels” were replaced with the explicit list of seven levels. Without the actual modified document, the requirement cannot be confirmed as satisfied.
- `T055` (rejected 1x): No updated `spec.md` file is provided, and there is no evidence that FR‑006’s description was edited to replace “Repeated Measures ANOVA” with “Linear Mixed-Effects Modeling (LMM)”. The required artifact (the modified specification document) is missing.
- `T056` (rejected 1x): No spec.md file or its contents were provided, so there is no evidence that the “Assumptions” section was edited to replace “no authentication barriers” with “Requires MP_API_KEY environment variable.” The required artifact is missing, preventing verification that the task was completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

