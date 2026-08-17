# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010a` (rejected 1x): The required artifact `data/raw/source_ref_table2.csv` does not exist, so the source table was not fetched as specified. The task’s deliverable is missing.
- `T010b` (rejected 1x): The required files `data/raw/reference_substructures_raw.csv` and `data/raw/checksums.json` are both missing, so no checksum verification could be performed. The task’s core requirement is therefore unmet.
- `T010d` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/source_kinetic_table3.csv
- `T010e` (rejected 1x): The required files `data/raw/kinetic_dataset_raw.csv` and `data/raw/checksums.json` are missing, so no checksum verification could be performed. The task’s core artifact does not exist, making the claim unfulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

