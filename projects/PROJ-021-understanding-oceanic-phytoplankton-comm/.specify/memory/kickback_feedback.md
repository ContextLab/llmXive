# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): The provided `tests/contract/test_schemas.py` exists but is truncated and references a non‑existent `aligned_dataset.schema.yaml`; without the schema file the contract test cannot perform any validation. The required schema artifact is missing, so the task’s requirement is not met.
- `T011a` (rejected 1x): The required output file `data/raw/reanalysis.nc` does not exist on disk, so the reanalysis data was not fetched and saved as specified. The task’s core requirement is therefore unmet.
- `T011b` (rejected 1x): The required output file `data/raw/modis.nc` does not exist, so the MODIS data was not fetched and saved as specified. The task’s core requirement is unmet.
- `T011` (rejected 1x): The required output file `data/raw/seabass.csv` does not exist, so no data was fetched or saved. Without this artifact the task’s core requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

