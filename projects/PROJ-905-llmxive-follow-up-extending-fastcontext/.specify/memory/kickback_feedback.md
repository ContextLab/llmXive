# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007c` (rejected 1x): The `pilot_validation.py` script is incomplete (the shown code truncates before finishing the precision calculation and never computes a correlation or writes `pilot_correlation.json`). The provided `regularity_scores.csv` contains only 5 rows, not the required 20‑sample size, and the expected output file `data/processed/pilot_correlation.json` is missing. These gaps mean the task’s requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

