# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007b` (rejected 1x): The required `specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml` file does not exist (or is empty), so the schema was not updated as specified. The implementer must create the file with the appropriate `flavor_similarity` definition based on the ratified methodology.
- `T018` (rejected 1x): The required output file `data/processed/ingredient_pairs.csv` is missing, so the pipeline never produced the final dataset with imputed similarity scores and logged exclusion counts. Without this artifact, the task’s core requirement is not satisfied.
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: data/logs/vif_scores.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

