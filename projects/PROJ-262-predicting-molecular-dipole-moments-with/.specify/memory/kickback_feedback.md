# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): The repository contains the `create_subset.py` script that correctly implements deterministic shuffling with seed 42 and writes to `data/processed/subset_final.parquet`, but the required output file `subset_final.parquet` is absent, indicating the subset was never generated or saved. The task’s core deliverable (the parquet file) is missing.
- `T019` (rejected 1x): The required `data/reports/excluded_molecules.csv` file does not exist, nor does the `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` file. The provided `handle_missing_coords.py` script is incomplete (truncated) and never writes the CSV or updates the YAML with an artifact hash. The task’s deliverables are therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

