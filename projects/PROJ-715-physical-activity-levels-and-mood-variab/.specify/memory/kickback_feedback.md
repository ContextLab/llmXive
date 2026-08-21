# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T024b` (rejected 1x): No `model_results.json` file is present in the provided evidence, and no content consolidating fixed effects, random effects, diagnostics, LOPO results, or sensitivity analysis is shown. The required aggregated JSON artifact is missing, so the task is not satisfied.
- `T025` (rejected 1x): The `data/processed/model_results.json` file exists, but the required `model_results.schema.yaml` is missing, so the contract cannot be validated against the schema. Without the schema, we cannot confirm that all required fields are present, and the provided test only checks a minimal structure, not full schema compliance. The task therefore remains incomplete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

