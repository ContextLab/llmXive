# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The repository lacks the required `data/results/variable_load_metrics.json` file, and `validate_variables()` does not itself read `required_variables.yaml` nor write the metrics JSON before exiting. Additionally, the referenced `dataset.schema.yaml` is missing, so the function cannot verify variables against the schema as specified. The implementation therefore does not meet the task’s full requirements.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

