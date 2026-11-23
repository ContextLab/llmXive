# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): Checked `src/data/download.py` (uses dataset `chrisvoncsefalvay/vaers-outcomes` instead of the required `"vaers/vaers2020_2023"`), the generated `data/raw/vaers_2020_2023.parquet` (size > 0) and `data/checksums.txt` (checksum line present). The wrong dataset source violates the task specification, so the requirement is not fully satisfied.
- `T003` (rejected 1x): Requested task execution failed; rerun successfully: src/data/validate_raw.py exit=1

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

