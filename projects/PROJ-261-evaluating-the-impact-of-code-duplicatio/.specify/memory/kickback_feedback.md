# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The repository contains a `main.py` with functions to compute and save the metrics and a join‑validation routine, but the `run_pipeline` implementation is truncated and the required output files `data/processed/clone_metrics.csv` and `data/processed/perplexity_scores.csv` are not present. Without a complete pipeline that actually creates those CSVs, the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

