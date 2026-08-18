# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T053` (rejected 1x): The repository contains `code/data/simulation.py`, but the script does not create the required `data/processed/simulated_data.csv` (the file is missing) and appears to stop after the ingest step, producing `merged_data.csv` instead of the specified output. Consequently the deliverable does not meet the task’s verification requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

