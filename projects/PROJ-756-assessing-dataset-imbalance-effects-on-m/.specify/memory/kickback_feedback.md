# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure (`projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/`, `data/`, `code/`, `tests/`, `artifacts/`, `results/`, `state/`) was presented or can be verified; the response contains no file listings or contents confirming their existence. The task therefore remains unfulfilled.
- `T006` (rejected 1x): No code, scripts, or files implementing the required data downloaders, saving raw CSV/Parquet to `data/raw/`, or performing checksum verification were provided. The artifact needed to demonstrate the functionality is missing, so the task is not satisfied.
- `T012` (rejected 1x): The test file `tests/contract/test_dataset_schema.py` exists, but the required schema file `contracts/dataset.schema.yaml` is missing, so the test cannot actually validate the processed data against the contract. The missing schema prevents the task from being fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

