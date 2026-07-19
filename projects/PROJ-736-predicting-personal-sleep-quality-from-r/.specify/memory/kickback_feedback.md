# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): The `download_hcp.py` script is truncated, contains a placeholder checksum, and does not implement downloading of the minimally preprocessed CIFTI files. Moreover, the required output file `data/raw/behavioral/hcp1200_behavioral_data.csv` is missing from the repository. The task’s requirements are therefore not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

