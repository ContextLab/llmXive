# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T057` (rejected 1x): The repository contains a `code/utils/checksums.py` file, but it never gets invoked after the survey app writes to `data/raw/submissions.csv` (no call to the checksum module is visible in `code/survey/app.py`). The raw submissions CSV itself is missing, and `code/analysis/00_preprocess.py` only defines checksum functions without actually using them to verify the file before processing. To satisfy the task, the app must trigger the checksum computation after each append, the preprocess script must perform the verification and raise an error on mismatch, and a real `submissions.csv` (or a placeh

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

