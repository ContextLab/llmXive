# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): The `tests/contract/test_schemas.py` file exists and contains a test that checks for `aligned_dataset.schema.yaml`, but the required schema file is missing, so the contract test cannot succeed. Additionally, the test file is truncated (the last function is incomplete), which would cause a syntax error. The missing `aligned_dataset.schema.yaml` (and the incomplete test code) must be provided for the task to be truly complete.
- `T011b` (rejected 1x): The required artifact `data/raw/modis.nc` is missing; no file was created or provided, so the task of fetching MODIS data to that location was not fulfilled.
- `T011c` (rejected 1x): The required output file `data/raw/seabass.csv` is missing, so no data was fetched or saved as specified. The task’s core requirement is not satisfied.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: code/01_data_ingestion.py, data/raw/seabass_filtered.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

