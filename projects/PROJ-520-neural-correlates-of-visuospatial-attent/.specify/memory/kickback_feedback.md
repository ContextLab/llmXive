# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T051#1` (rejected 1x): The required artifact `data/processed/metadata.json` is missing entirely, so there is no way to verify the presence or correctness of the `data_source_url` and `fetch_method` fields or the absence of synthetic fallback data. The implementer must create the file with the appropriate fields and ensure it contains no synthetic data.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

