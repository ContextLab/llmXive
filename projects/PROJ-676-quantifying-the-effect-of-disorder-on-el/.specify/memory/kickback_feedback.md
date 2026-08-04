# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The integration test file `tests/integration/test_pr_scaling.py` is present, but the required output `data/processed/scaling_fits.json` does not exist, so the test cannot pass and the schema validation cannot be performed. The missing JSON file must be generated (or added) for the task to be satisfied.
- `T013b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/pr_raw_multiL.json
- `T033a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/w0_results.json, data/processed/scaling_fits.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

