# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: data/metadata.yaml
- `T008a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/download_guild_source.py, data/metadata.yaml, data/raw/guild_source.csv
- `T008b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/generate_guild_mapping.py, data/raw/guild_source.csv, data/processed/guild_mapping.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

