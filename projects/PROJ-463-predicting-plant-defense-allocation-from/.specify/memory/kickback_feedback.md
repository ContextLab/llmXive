# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011a` (rejected 1x): The repository contains `src/data/verify_metadata.py`, but the file is truncated and does not show logic that writes `data/processed/metadata_verification_report.json`. Moreover, the required JSON report is missing from the filesystem, indicating the implementation does not fulfill the output requirement. The next implementer should complete the script (including verification of tissue, herbivore type, and replicates) and ensure it always creates the `metadata_verification_report.json` file in `data/processed`.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

