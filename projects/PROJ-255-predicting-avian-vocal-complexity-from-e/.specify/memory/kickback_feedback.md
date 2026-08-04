# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): There are no unit test files, test suites, or any code artifacts provided that target the project's configuration or logging utilities. The only evidence shown relates to avian vocal‑complexity feature specifications, not to unit tests for config/logging, so the required tests are missing.
- `T015` (rejected 1x): The required output files `data/interim/noise_mapped.csv` and `data/interim/dropped_missing_osm.csv` are not present on disk, so the task’s deliverables are missing despite the presence of `src/data/acquisition.py`.
- `T015c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/interim/validation_log.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

