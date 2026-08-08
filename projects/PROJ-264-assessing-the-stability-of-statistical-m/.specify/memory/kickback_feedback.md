# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): No artifact (code, notebook, data file, or result output) was provided that shows the log‑log linear regression of log(CV) on log(n_samples) and log(n_features), nor any computed residuals or confirmation that Pearson r remains the primary output. The claim lacks any concrete evidence of the required computation.
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: results/stability_metrics.csv, results/correlation_results.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

