# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014a` (rejected 1x): The repository contains a large `code/ingestion.py`, but it does not include a concrete routine that reads the raw driving logs from `data/raw/`, aligns timestamps, and writes the required `data/derived/driving_signals.csv`. Moreover, the expected output file `data/derived/driving_signals.csv` is absent. The task’s core output is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

