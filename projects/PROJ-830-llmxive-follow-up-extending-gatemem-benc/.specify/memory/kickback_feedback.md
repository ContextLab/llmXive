# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006b` (rejected 1x): The required file `src/utils/data_loader.py` does not exist, and the referenced schema file `contracts/dataset.schema.yaml` (or `schema.yaml`) is also missing, so no validation logic was added. The implementer must create/modify the data_loader module and include the schema file to perform the required checks.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/profiling.py
- `T008a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/stats.py
- `T008b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/stats.py
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/gatekeeper/pipeline.py
- `T010` (rejected 1x): The `tests/contract/test_dataset_schema.py` file is present, but it relies on `contracts/dataset.schema.yaml`, which does not exist in the repository, so the tests cannot actually load or validate against the schema. Without the schema file, the test suite cannot run successfully, meaning the task’s requirement is not genuinely satisfied.
- `T011` (rejected 1x): The provided `tests/contract/test_results_schema.py` attempts to load `contracts/results.schema.yaml`, but that schema file is missing from the repository, so the test cannot actually validate any output. Additionally, the displayed contents of the test file are truncated, indicating the implementation may be incomplete. The task’s requirement of having a functional contract test against an existing `results.schema.yaml` is not met.
- `T015a` (rejected 1x): The required file `src/gatekeeper/rules.py` does not exist in the repository, so the requested regex‑based rule engine is missing entirely. The implementer must add this file with the specified functionality.
- `T015b` (rejected 1x): The required file `src/gatekeeper/rules.py` does not exist, so no code handling malformed deletion log entries or logging to `logs/deletion_errors.log` is present. The task’s core artifact is missing.
- `T012` (rejected 1x): The required artifacts `data/processed/access_control_results.json` and `results.schema.yaml` (or `schema.yaml`) are missing from the repository, so no verification can be performed. The task cannot be considered done until both files exist and are validated against each other.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

