# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T029` (rejected 1x): The repository lacks the required input file `results/simulation_results.csv` and the output file `results/aggregate_metrics.csv`. Moreover, the provided excerpt of `code/analysis/metrics.py` does not show an implementation of `calculate_aggregate_metrics`, so the core functionality is absent. The next implementer must create the simulation results CSV (or ensure T028c generates it) and add a fully working `calculate_aggregate_metrics` that writes the specified aggregate metrics with Clopper‑Pearson confidence intervals.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

