# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017c` (rejected 1x): The repository contains a `02_preprocessing_merge.py` script, but the merged CSV `data/processed/merged_monthly.csv` is absent and the referenced schema file `contracts/dataset.schema.yaml` does not exist. Moreover, the script excerpt shows no concrete validation against the schema. The required output and validation artifact are missing, so the task is not fully satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

