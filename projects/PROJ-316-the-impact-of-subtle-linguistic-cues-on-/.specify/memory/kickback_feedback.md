# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001c` (rejected 1x): The `data/raw/rater_metadata.json` correctly contains the Cohen's Kappa metrics, but the required `data/processed/ratings.csv` file is missing, so the core deliverable of the task is not present. The pipeline cannot be considered complete until the ratings CSV with the specified columns is generated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

