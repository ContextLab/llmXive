# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T030b` (rejected 1x): The repository lacks the required input files (`data/validation/human_annotations.csv` and `data/derived/stress_curves.parquet`), and the shown portion of `code/metrics.py` does not contain any implementation of the HVCM calculation described in the task. Consequently the primary regression target is not derived as specified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

