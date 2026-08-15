# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The provided `tests/contract/test_dataset_schema.py` does not contain the required `test_schema_validation_passes(df)` implementation (the file ends before any test functions are defined), and the referenced schema file `contracts/dataset.schema.yaml` is absent from the repository. Both the test logic and the schema it should validate against are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

