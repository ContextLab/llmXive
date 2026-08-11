# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the requested `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/{data,models,viz,notebooks,utils,tests}` directory tree (or any `mkdir`/`touch` commands) was provided; the response contains only the task description and no file or folder listings. The required folder hierarchy is therefore missing.
- `T001b` (rejected 1x): declared artifact(s) missing/empty/invalid: requirements.txt
- `T002` (rejected 1x): The required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/requirements.txt` file is missing, and there is no evidence that `python --version` was run to confirm a 3.11.x interpreter. The implementer only provided a similarly named file in a different location and no version verification.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

