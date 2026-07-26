# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): The required source files `data/clean.py` and `data/lag.py` are absent from the repository, so they cannot be integrated into `main.py`. Without these modules (and any verification of `analysis/correlation.py` usage), the pipeline for US‑1 is not present. The task therefore remains unfinished.
- `T043` (rejected 1x): declared artifact(s) missing/empty/invalid: results/us1_correlation.json, results/plot_scatter.png, results/plot_timeseries.png, results/quality_log.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

