# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/merged_dataset.csv, data/processed/excluded_species_summary.csv, data/logs/species_exclusions.log
- `T024` (rejected 1x): No `artifacts/model_metrics.json` file was presented; the response contains no JSON content, schema, or metric values. Consequently the required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

