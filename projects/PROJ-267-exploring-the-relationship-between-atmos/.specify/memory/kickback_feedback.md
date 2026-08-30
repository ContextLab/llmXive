# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017c` (rejected 1x): The repository contains a `02_preprocessing_merge.py` script, but the required output file `data/processed/merged_monthly.csv` does not exist, and the referenced schema file `contracts/dataset.schema.yaml` is also missing. Consequently the script cannot perform the required validation or save the merged CSV as specified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

