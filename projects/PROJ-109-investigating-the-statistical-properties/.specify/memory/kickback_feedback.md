# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The implementer provided only narrative user stories and no evidence of the required directories (`code/data`, `code/analysis`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`, `docs`). Since the artifact (the project folder hierarchy) is missing, the task is not satisfied.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: code/config.py
- `T008` (rejected 1x): The repository contains `code/data/synthetic_generator.py` with a fixed seed, the required concentration offset, and code to write an HDF5 file, but the expected output file `data/raw/synthetic_halos.h5` is absent, so the required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

