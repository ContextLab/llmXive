# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): The `schema_validator.py` file exists and contains validation logic, but the required schema file `contracts/dataset.schema.yaml` is missing, so the validator cannot actually perform the intended checks. Add the missing YAML schema at the specified path (or provide it) to satisfy the task.
- `T031` (rejected 1x): No code, notebook, data files, or result outputs for the “permutation importance correlation analysis” were provided. The claim lacks any artifact (e.g., script computing permutation importance, correlation plots, or a report) that could be inspected to confirm the analysis was performed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

