# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004b` (rejected 1x): No `spec.md` file or any excerpt showing the corrected SC-005 section is provided; the required artifact is missing, so the task of fixing the corrupted text cannot be verified as completed.
- `T007` (rejected 1x): No directory structure (`data/raw/`, `data/processed/`, `data/models/`, `logs/`) is shown or referenced in the provided artifacts; the implementer gave no file listings, screenshots, or code that creates these folders. The required folder hierarchy is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

