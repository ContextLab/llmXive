# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The `validation.py` file is present and contains logic to compute dielectric deviations, but the required `solvents.yaml` reference file is missing, so the code cannot actually perform the comparison. Without the lookup table the module cannot flag runs >2% deviation, violating the task’s requirement. The missing `solvents.yaml` must be added (or the code adjusted to handle its absence) for the task to be complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

