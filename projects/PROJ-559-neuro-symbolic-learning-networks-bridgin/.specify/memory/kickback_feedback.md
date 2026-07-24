# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T041` (rejected 1x): No documentation files were presented in the `docs/` directory, nor any excerpt showing an explanation of symbolic versus neural boundaries. Without concrete evidence of the required documentation update, the task’s deliverable is missing.
- `T042` (rejected 1x): No code, diff, or documentation showing that any cleanup or refactoring was performed is present; the only material provided is a feature specification unrelated to “code cleanup and refactoring.” The required artifacts (e.g., cleaned source files, refactoring commit logs, before‑and‑after comparisons) are missing, so the task is not satisfied.
- `T043` (rejected 1x): No artifacts (e.g., CI workflow logs, memory profiling reports, or optimized code changes) were provided to demonstrate that the pipeline now runs within a ≤7 GB RAM limit. Consequently, there is no evidence that the required performance optimization across all stories has been achieved.
- `T044` (rejected 1x): No unit test files were found in the `code/tests/unit/` directory; the implementer provided no evidence of additional tests being added, so the required artifact is missing.
- `T045` (rejected 1x): No validation report, log, or any artifact showing that `quickstart.md` was actually checked is present; the implementer provided no evidence that the required validation step was performed.
- `T046` (rejected 1x): No CI resource monitoring reports, logs, or screenshots are present to demonstrate that the pipeline was executed on a fresh runner and that CPU and memory usage stayed within the required limits. The required artifact (resource usage evidence) is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

