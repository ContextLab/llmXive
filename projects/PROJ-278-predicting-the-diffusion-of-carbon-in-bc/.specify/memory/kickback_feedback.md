# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004c` (rejected 1x): The required file `specs/001-predict-carbon-diffusion-bcc/contracts/split_config.schema.yaml` does not exist, so none of the specified fields (`strategy`, `n_samples`, `warning_emitted`) are defined. The task cannot be considered done until the schema file is created with the correct field definitions.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

