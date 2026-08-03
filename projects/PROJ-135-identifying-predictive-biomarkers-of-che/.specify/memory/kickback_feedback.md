# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The `tests/contract/test_data_schema.py` file exists, but the required `dataset.schema.yaml` file is missing, causing the existence test to fail. Moreover, the test does not implement the synthetic‑sample validation (checking that valid data passes and invalid data fails) that the task explicitly required. Both the missing schema artifact and the incomplete test logic mean the requirement is not satisfied.
- `T011` (rejected 1x): The provided test file is truncated and does not contain assertions verifying the existence or exact JSON content, nor does it include a test for the GEO‑insufficient scenario. The helper `_write_mock_state` is a stub (`pass`). Consequently, the integration test does not actually confirm that T014 writes `data/feasibility_gate.json` correctly for either required case, and the expected output file is missing. The next implementer must add complete assertions for both scenarios and ensure the file content matches the specified status/reason values.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_acquisition.py, state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_acquisition.py
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: src/preprocessing.py
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: src/differential_expression.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

