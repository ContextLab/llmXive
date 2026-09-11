# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): The repository contains `code/scripts/generate_assets.py`, but the required output files (`data/assets/img_00.png` … `img_20.png` and `data/assets/manifest.json`) are absent, indicating the script has not been executed or does not produce the needed assets. The missing images and manifest mean the task’s core deliverables are not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

