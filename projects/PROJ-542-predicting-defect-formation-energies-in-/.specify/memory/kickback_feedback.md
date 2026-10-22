# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): Requested task execution failed; rerun successfully: src/data/download.py exit=1
- `T006` (rejected 1x): The split implementation exists, but the required output artifacts are absent: `data/processed/train.csv`, `data/processed/test.csv`, `data/checksums/train.sha256`, and `data/checksums/test.sha256` are all missing, so the deterministic split and checksum generation have not been materialized.
- `T007` (rejected 1x): Requested task execution failed; rerun successfully: src/models/train.py exit=1

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

