# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005a` (rejected 1x): The provided `tests/unit/test_schema_validation.py` is truncated and does not contain the required `test_structural_metric_fallback_logic` test, and the referenced `contracts/structural_metric.schema.yaml` file is missing entirely, so the conditional logic cannot be verified. The task needs a complete test file and the actual schema file.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

