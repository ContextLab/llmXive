# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The `code/download.py` script contains a hard‑coded `limit: 300`, never updates the offset for pagination, never writes the collected records to `data/raw/occurrence_1970_2000.csv`, and does not read the species list from `code/config.py`. Moreover, the required CSV file is missing.
- `T013b` (rejected 1x): The required `data/raw/occurrence_2005_2020.csv` file is missing, and the provided `code/preprocess.py` excerpt shows no logic that reads this CSV, counts records per species, or appends entries to `metrics/data_sufficiency.json` as specified. Consequently the task’s core requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

