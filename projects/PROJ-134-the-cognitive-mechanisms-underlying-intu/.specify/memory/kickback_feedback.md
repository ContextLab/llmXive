# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016b` (rejected 1x): No code, data, or documentation artifacts were presented to demonstrate that US1 (data ingestion and preprocessing) has been implemented, nor any evidence of schema validation, mapping to VR salience conditions, or quality checks. Without tangible artifacts, the claim cannot be verified as meeting the task requirements.
- `T054c#1` (rejected 1x): No artifacts (code, data files, logs, or results) were provided showing that real VR interaction logs were fetched, processed, and used to verify the VR salience mapping. Consequently, the requirement to validate the mapping with actual data is not demonstrated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

