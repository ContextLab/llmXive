# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T024` (rejected 1x): The required output file `data/interim_lagged_mmns.csv` does not exist, and the provided `src/data/align.py` snippet shows only placeholder comments about MMN windows without any implementation of the lagged‑alignment calculation or CSV writing. The task’s deliverable is therefore not satisfied.
- `T025` (rejected 1x): No code, script, or data artifact was provided that shows exclusion of blocks with fewer than 10 valid trials or NaN handling for excessive artifact rejection, nor is there an `aligned_data.csv` output demonstrating the lagged alignment with underpowered subjects excluded. The required implementation and resulting files are missing.
- `T026` (rejected 1x): declared artifact(s) missing/empty/invalid: data/interim_lagged_mmns.csv, data/accuracy_blocks.csv, data/aligned_data.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

