# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): The repository contains a partially implemented `code/metrics/extract.py`, but it does not include code that walks `data/training/` and `data/held_out/`, computes the three metrics for each trace, and writes them to `data/processed/feature_matrix.csv`. Moreover, the required CSV file is absent. The task’s primary deliverable is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

