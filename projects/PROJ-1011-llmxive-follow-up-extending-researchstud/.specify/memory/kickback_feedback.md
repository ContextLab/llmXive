# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T049` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/unit/test_streaming_logic.py
- `T050` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/unit/test_pattern_mapping.py
- `T051` (rejected 1x): The required test file `tests/unit/test_evaluation_loader.py` does not exist, so the `test_blind_evaluation_metadata_stripping` implementation is missing entirely. Without this file, the assertion about metadata stripping cannot be verified.
- `T049#1` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/unit/test_streaming_logic.py
- `T050#1` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/unit/test_pattern_mapping.py
- `T051#1` (rejected 1x): The required test file `tests/unit/test_evaluation_loader.py` does not exist, so the implementation of `test_blind_evaluation_metadata_stripping` is missing entirely. Without this artifact, the task’s assertion and fixture cannot be verified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

