# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The required artifact `tests/integration/test_us1_pipeline.py` does not exist in the repository, so the integration test for the US1 pipeline on 2 subjects is missing. The task cannot be considered completed until this test file is added with appropriate test code.
- `T023c` (rejected 1x): The provided `code/connectivity_engine.py` only contains utilities for loading/saving connectivity matrices and does not implement L‑regularized logistic regression feature selection on PCA components nor write `data/derived/connectivity_features_reduced.csv`. Moreover, the required output CSV file is absent from the repository.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

