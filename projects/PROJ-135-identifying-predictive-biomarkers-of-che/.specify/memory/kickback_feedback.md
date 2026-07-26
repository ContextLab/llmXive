# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The required integration test file `tests/integration/test_acquisition.py` does not exist in the repository, so the specified end‑to‑end download, normalization, and splitting test is absent. The task cannot be considered fulfilled until this test script is added with the appropriate assertions.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_acquisition.py
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_acquisition.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

