# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009c` (rejected 1x): The repository lacks the required input files `data/raw/mp_alloys.json` and `data/raw/nist_alloys.json`, and the expected output `data/processed/merged_raw.parquet` is not present. Moreover, the provided `code/merge.py` is truncated and does not show the full merge, deduplication, conflict‑resolution, or parquet‑writing logic required by the task. These missing artifacts must be added and the script completed for the task to be considered done.
- `T016` (rejected 1x): The repository contains `code/data/clean.py`, but it does not show a dedicated function that appends exclusion records to `data/logs/exclusion_log.txt` in the required CSV format, nor is the `exclusion_log.txt` file present. Without the logging utility implementation and the output file, the task’s requirement is not satisfied.
- `T015c` (rejected 1x): The repository lacks the required `data/processed/alloys_clean.parquet` file, and the provided `code/data/clean.py` does not contain logic to serialize a cleaned dataset, perform a row‑count check, call `sys.exit(1)`, or log an error when the count is < 50. Consequently the task’s serialization and validation requirements are not met.
- `T019` (rejected 1x): The repository lacks the required `data/processed/alloys_ilr.parquet` file, and the shown portion of `code/data/clean.py` does not contain any implementation that applies the `compositional.ilr` transformation to the specified elements or writes the transformed data to that parquet file. The task’s core functionality and output are therefore missing.
- `T028` (rejected 1x): The `code/analysis.py` file does not contain any function that computes variance inflation factors on ILR‑transformed features, despite importing `variance_inflation_factor`. Moreover, the required input file `data/processed/alloys_ilr.parquet` is absent, so the VIF calculation cannot even be run. Both the implementation and the necessary data are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

