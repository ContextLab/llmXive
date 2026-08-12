# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): The provided `code/utils/check_weights.py` is truncated (the `main()` function ends abruptly) and does not contain the logic to load the manifest, iterate over listed weight files, or exit with the required status codes. Moreover, there is no handling shown for a missing `weights_manifest.json` or for aborting with a clear error when the ground‑truth parquet file is absent. Consequently the script does not demonstrably satisfy the task’s specifications.
- `T009` (rejected 1x): No JSON schema files for `TeacherRoutingDataset`, `InferenceResult`, or `DecisionTreeMetadata` were presented in `specs/contracts/`; the required artifacts are missing, so the task is not satisfied.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/integration/test_data_generation.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

