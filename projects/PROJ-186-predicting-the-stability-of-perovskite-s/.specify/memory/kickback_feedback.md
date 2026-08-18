# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The repository contains `code/data/preprocess.py`, but the required output file `data/processed/features.csv` is missing; without this CSV the verification step cannot succeed. The implementer must generate and commit the cleaned `features.csv` (or provide a way to produce it) so the task’s artifact exists.
- `T018` (rejected 1x): The required artifact `data/processed/features.csv` does not exist, so the assertion cannot be run and the null‑check cannot be verified. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

