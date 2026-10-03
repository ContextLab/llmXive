# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): No configuration files, scripts, or documentation were presented to show that API keys and data paths are managed via environment variables, a `.env` file, or a configuration management system. The required artifact for task T006 is missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/data_validation.py
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/retry_policy.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

