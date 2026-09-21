# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T038` (rejected 1x): No `docs/` files or `paper/draft.md` were presented, and there is no evidence that these documents were updated to include CI vs Research mode labeling. The required documentation artifacts are missing.
- `T039` (rejected 1x): No code, diff, or documentation artifacts showing that any cleanup or refactoring was performed are present; the claim lacks any tangible evidence (e.g., updated source files, commit logs, before‑after comparisons) to verify the work. The required deliverables are missing.
- `T040` (rejected 1x): No code, script, or documentation was provided that implements chunked processing for FID/LPIPS, nor any memory‑usage or benchmark evidence showing the computation stays within the 7 GB RAM limit. The required artifact demonstrating the performance optimization is missing.
- `T041` (rejected 1x): No evidence of any files or content under `tests/unit/` was provided; the claim lacks the required unit test artifacts, so the task of adding additional unit tests is not demonstrated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

