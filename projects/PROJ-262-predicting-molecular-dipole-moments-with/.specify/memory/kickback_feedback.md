# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019a` (rejected 1x): The required output file `data/reports/excluded_molecules.csv` is not present, and the provided `handle_missing_coords.py` is truncated before the logic that writes the CSV is shown, so the filtering/exclusion implementation is incomplete. The next implementer must finish the script to generate the CSV with the specified columns and ensure the file is created.
- `T016a` (rejected 1x): The script `create_subset.py` correctly implements deterministic subset creation with seed 42 and size 5000, but the required output file `data/processed/subset_final.parquet` is missing, so the task’s primary artifact is not present. The implementer must run the script (or otherwise generate) to produce the parquet file at the specified location.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

