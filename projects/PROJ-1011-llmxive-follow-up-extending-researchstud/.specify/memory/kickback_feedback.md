# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): The required test file `tests/unit/test_memory_usage_constraint.py` is missing from the repository, so no test code exists to verify the memory usage constraint. Without this artifact, the task is not satisfied.
- `T019` (rejected 1x): The required test file `tests/unit/test_preprocessing_validation.py` does not exist in the repository, so there is no artifact to verify that abstracts are non‑empty. Without this file, the preprocessing validation test cannot be run, meaning the task’s requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

