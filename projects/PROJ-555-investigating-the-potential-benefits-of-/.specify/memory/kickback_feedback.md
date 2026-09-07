# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006c` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): The response contains only the task description and project specifications; it does not include any actual directory tree, created folders, or `.gitkeep` files for `data/raw/landsat`, `data/processed`, or `data/ecotourism`. Without these artifacts, the requirement of establishing the data directory structure is not satisfied.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/climate_covariates.parquet

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

