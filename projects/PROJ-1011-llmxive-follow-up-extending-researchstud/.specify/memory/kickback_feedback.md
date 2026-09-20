# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): The required test file `tests/unit/test_memory_usage_constraint.py` is missing from the repository, so no evidence exists that the memory‑usage constraint has been tested. The implementer must add the specified test file with appropriate assertions.
- `T019` (rejected 1x): The required test file `tests/unit/test_preprocessing_validation.py` does not exist in the repository, so the validation test for non‑empty abstracts is missing. Without this artifact, the task’s requirement is not satisfied.
- `T040` (rejected 1x): The required test file `tests/unit/test_multiple_comparison_correction.py` is missing from the repository, so no test code for Bonferroni or Benjamini‑Hochberg correction exists to satisfy the task. The artifact must be added with appropriate unit tests.
- `T043` (rejected 1x): No updated files in the `docs/` directory or modifications to `README.md` are provided; the claim contains only a feature specification and test scenarios, with no actual documentation artifacts to verify. The required documentation updates are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

