# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014a` (rejected 1x): The provided `code/compute_metrics.py` does not show a `compute_physical_descriptors(cif_path)` function, and the required log file `results/power_analysis.log` is absent. Consequently the physical descriptor calculations are not implemented nor logged as specified.
- `T016` (rejected 1x): The `results/correlations.json` file is empty (`[]`) instead of containing Pearson and Spearman coefficients, the required state YAML file is missing, and the provided `code/analyze.py` does not include any implementation that computes the requested correlations or writes them to the JSON file. These missing/placeholder artifacts prevent the task from being considered complete.
- `T021` (rejected 1x): The repository lacks the required output artifacts (`results/power_analysis.log`, `data/processed/filtered_features.csv`, and the state YAML file), and the shown portion of `code/analyze.py` does not contain an implementation of `filter_features` that performs VIF‑based filtering, logging, CSV writing, or checksum updating. These essential components are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

