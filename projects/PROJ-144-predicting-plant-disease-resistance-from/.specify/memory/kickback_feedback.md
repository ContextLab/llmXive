# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012a` (rejected 1x): The repository contains `code/research/verify_studies.py`, but the script is truncated and never writes to `data/raw/study_manifest.json`. Moreover, the required `data/raw/study_manifest.json` file is missing entirely, so the task’s core output does not exist. The implementer must add code to save the manifest JSON and ensure the file is created, non‑empty, and contains valid URLs.
- `T012b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/study_manifest.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

