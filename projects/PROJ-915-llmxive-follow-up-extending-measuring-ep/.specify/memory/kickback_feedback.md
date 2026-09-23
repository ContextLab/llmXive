# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): The repository lacks the required `data/raw/medmis_subset.csv` file, and `state/artifact_hashes.yaml` contains only a placeholder hash instead of a real SHA‑256 checksum. Moreover, the provided `code/ingestion.py` is truncated and does not show the CSV‑writing or checksum‑recording logic, indicating the implementation is unfinished. The task’s core output artifacts are therefore missing.
- `T015` (rejected 1x): The provided `code/features.py` is truncated and does not contain logic to flag undefined imperative ratios, add an `is_ratio_undefined` column, or write the processed data to `data/processed/features.csv`. Moreover, the required output file `data/processed/features.csv` is absent. The task’s core requirement is therefore unmet.
- `T017a` (rejected 1x): The repository lacks the required input `data/raw/medmis_subset.csv` and the expected output `data/raw/human_pilot_cached.csv`. Moreover, `code/annotation.py` is truncated and does not show a complete implementation of the deterministic pilot generation logic. The implementer must provide the missing CSV, finish the script to generate the 50‑row dataset with the specified columns, and ensure the file is created when absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

