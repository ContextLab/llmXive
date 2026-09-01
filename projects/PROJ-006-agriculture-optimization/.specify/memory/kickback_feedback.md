# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The provided `synthetic_generator.py` does not produce all required columns (e.g., `village_id` is missing, column names `CSA_Index`, `Stability_Score`, and `HFIAS` are mismatched in case), and it does not use a multivariate normal distribution for the continuous variables as specified. Moreover, the referenced `contracts/dataset.schema.yaml` file is absent, so the generator cannot be validated against the schema.
- `T041a` (rejected 1x): The provided artifacts show the pipeline script but the required output file `data/processed/analysis_dataset.csv` is missing, and there is no evidence of a successful run (exit code 0, row count >300, or CI execution). The task’s core verification steps have not been demonstrated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

