# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007a` (rejected 1x): The required schema file `contracts/dataset.schema.yaml` does not exist (only a missing `schema.yaml` is noted), so the explicit field definitions are absent. The task’s core artifact is missing, making the implementation incomplete.
- `T007b` (rejected 1x): The repository lacks the required `contracts/dataset.schema.yaml` file, so the validation code cannot actually enforce the schema. Moreover, the provided `validate_schema.py` excerpt does not show a `validate_schema(dataframe)` function that raises `InsufficientDataError` as specified, leaving its implementation unverified. The missing schema file and uncertain presence of the required function mean the task is not genuinely completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

