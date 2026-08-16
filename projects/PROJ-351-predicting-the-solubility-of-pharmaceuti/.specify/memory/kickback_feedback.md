# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No evidence of a logging configuration or any files under `data/logs/` was provided; the required artifact (logging infrastructure capturing exclusion counts and training metrics) is missing. The implementer must add the appropriate logging setup and ensure logs are written to the specified directory.
- `T009` (rejected 1x): No evidence of a seed‑configuration file or code (e.g., a `seed_config.py`, JSON/YAML settings, or similar) located in a `code/` directory is provided; the claim lacks any artifact showing that random seeds are pinned and managed. The required environment‑configuration implementation is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

