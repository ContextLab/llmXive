# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000a` (rejected 1x): No `research.md` file was provided at the required path, and no schema definition for the “Verified datasets” section (with fields `dataset_id`, `title_token_overlap`, `checksum`, `verification_date`) is present in the evidence. The implementer must create the file with the specified YAML/JSON schema.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

