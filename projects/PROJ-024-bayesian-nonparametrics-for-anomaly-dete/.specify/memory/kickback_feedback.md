# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T060` (rejected 1x): The required source file `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml` is missing, so the migration script could not move the `dataset_stats`, `inference_results`, and `simulation_metrics` keys. Consequently no actual migration occurred and the size check on the intended config file cannot be performed. The existing `code/config.yaml` is unrelated to the task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

