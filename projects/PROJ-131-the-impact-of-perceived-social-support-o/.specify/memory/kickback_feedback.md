# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T072b` (rejected 1x): No evidence of the file `specs/001-social-support-resilience/spec.md` being present or showing the required changes (removal of FR-001/FR-002 and the “Synthetic Cohort” narrative) was provided. The implementer’s claim cannot be verified without the actual updated spec content.
- `T073b` (rejected 1x): No actual `specs/001-social-support-resilience/spec.md` file content or diff was provided, so we cannot verify that the Data Dictionary was updated as required. The claim lacks concrete artifact evidence.
- `T074b` (rejected 1x): No content from `specs/001-social-support-resilience/spec.md` (or any indication that Section 5 was edited) was provided; without the updated specification file we cannot confirm the methodological notes were revised as required. The required artifact is missing.
- `T008` (rejected 1x): No `main_pipeline.py` file or any code snippet was provided; thus there is no evidence that an entry‑point script orchestrating the modular pipeline steps was created. The required skeleton is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

