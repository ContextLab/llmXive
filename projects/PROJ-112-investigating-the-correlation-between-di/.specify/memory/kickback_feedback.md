# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory tree or file listing was provided; the implementer did not supply any artifact showing that a project directory structure was created. The required folder hierarchy is missing, so the task is not satisfied.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/ingestion/agp_loader.py
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/ingestion/ukbb_loader.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

