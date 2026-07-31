# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T042` (rejected 1x): The required schema files `contracts/synthetic_image.schema.yaml` and `contracts/regression_result.schema.yaml` are missing (no `schema.yaml` present), so the task’s deliverables are not provided. The implementer must create these two YAML schema files with the specified properties.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

