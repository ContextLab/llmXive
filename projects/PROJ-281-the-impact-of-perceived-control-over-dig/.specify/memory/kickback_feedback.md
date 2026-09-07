# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T038` (rejected 1x): No evidence was presented showing that `specs/001-the-impact-of-perceived-control-over-dig/quickstart.md` exists or has been updated; without the actual documentation file we cannot verify that the required documentation changes were made.
- `T039` (rejected 1x): No code files (e.g., `proxy_extractor.py`) or diff showing the refactoring are present, so we cannot verify that text data is no longer accessed during proxy extraction. The required artifact demonstrating the cleanup is missing.
- `T040a` (rejected 1x): No evidence was provided that the file `specs/001-the-impact-of-perceived-control-over-dig/quickstart.md` exists, has been updated, or that validation errors have been resolved and all scenarios now pass. Without the artifact or test results, the claim cannot be confirmed.
- `T041` (rejected 1x): No performance profiling code, logs, or reports are present to demonstrate that the pipeline’s runtime is under 6 hours and RAM usage under 7 GB on a free‑tier runner, nor is there any flag indicating a conflict between Plan.md and Spec SC‑004. These required artifacts are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

