# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T039` (rejected 1x): The `code/stats.py` file is truncated and does not contain a full implementation that reads the required inputs, joins them, computes `network_density`, and writes `subject_metrics.csv`. Moreover, the prerequisite data files (`global_efficiency.json`, `rsfc.npy`, `motif_z_aggregated.json`) are absent, and the expected output CSV is missing. The placeholder `weighted_adjacency.npy` is just a text stub, not a real NumPy array. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

