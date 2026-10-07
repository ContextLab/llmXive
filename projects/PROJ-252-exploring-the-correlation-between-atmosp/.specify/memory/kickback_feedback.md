# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The `tests/integration/test_download_pipeline.py` file is present but truncated (e.g., the `required_fields` string is incomplete) and cannot run correctly. Moreover, the required `data/processed/config.yaml` file, which should define `expected_earthquake_count` (12), is missing entirely, so the test cannot obtain the expected count. Both artifacts needed to satisfy the task are absent or malformed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

