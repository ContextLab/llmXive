# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: code/config.py
- `T015` (rejected 1x): The `preprocess.py` file defines `load_schema` but does not import `jsonschema` nor call `jsonschema.validate` on the filtered DataFrame, and the `validate_schema` function is truncated and incomplete. Consequently, the required schema loading and validation step after filtering is not implemented.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

