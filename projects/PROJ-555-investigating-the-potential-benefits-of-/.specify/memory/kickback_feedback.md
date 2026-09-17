# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T045` (rejected 1x): No evidence of the `specs/001-ecotourism-regeneration/spec.md` file or its contents was provided, so we cannot verify that SC‑001 was updated from “[deferred]” to “30”. The required artifact and change are missing.
- `T006c` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No evidence of the required directories (`data/raw/landsat`, `data/processed`, `data/ecotourism`) or the accompanying `.gitkeep` placeholder files is provided; without these artifacts the task’s requirement is not satisfied.
- `T012b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/site_coordinates.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

