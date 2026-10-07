# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010b` (rejected 1x): The required `contracts/dataset.schema.yaml` file is not present on disk, and the provided `save_dataset_schema` function writes JSON (via `json.dump`) rather than a proper YAML document. Consequently the schema artifact does not exist in the expected format, so the task is not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

