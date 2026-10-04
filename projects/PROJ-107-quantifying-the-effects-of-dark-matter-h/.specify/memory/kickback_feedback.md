# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The repository lacks the required output files `data/processed/halo_shapes.csv` and `data/processed/exclusion_log.json`, and the provided `pipeline_runner.py` does not contain the aggregation, validation, logging, or CSV‑writing logic described in the task. The implementer must add the missing processing steps and generate the two deliverable files.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

