# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (code/, data/, results/, tests/) is provided; the implementer did not supply a directory listing or any files showing that the structure has been created.
- `T003` (rejected 1x): The implementer supplied only a feature specification for a spatial‑reasoning experiment and no files or configuration related to linting/formatting. There is no `pyproject.toml`, `.ruff.toml`, `black` config, or any documentation showing ruff and black have been set up, so the required artifact is missing.
- `T006` (rejected 1x): The required output file `data/raw/synthetic_spatialclaw_v1.json` does not exist, so the generator script has not produced the dataset as specified. Consequently the task’s primary deliverable is missing.
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T011` (rejected 1x): No logging infrastructure code, configuration, or sample execution logs were provided. The claim lacks any artifact demonstrating that seed values and blocked operation details are captured, so the requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

