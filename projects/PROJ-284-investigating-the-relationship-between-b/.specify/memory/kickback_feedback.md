# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T022` (rejected 1x): The required output file `data/analysis/aggregated_metrics.csv` does not exist, and the provided `code/data/metrics.py` excerpt shows no logic for reading `metrics_raw.csv`, aggregating node‑level metrics, or writing the aggregated CSV. Consequently the task’s core requirement is unmet.
- `T023a` (rejected 1x): The repository lacks the required `data/analysis/aggregated_metrics.csv` input file, and consequently the expected output files `pca_loadings.csv` and `factor_scores.csv` are not present. Moreover, the provided `correlations.py` is truncated and does not contain any execution logic that would generate those outputs. The task’s required artifacts are missing.
- `T023b` (rejected 1x): The required output file `data/analysis/full_metrics.csv` is absent, and the `save_full_metrics` function in `code/analysis/correlations.py` is incomplete (no implementation). Consequently the task’s file‑output and metric‑preservation requirement is not satisfied.
- `T025` (rejected 1x): The repository lacks the required `data/analysis/fdr_corrected_results.csv` file, and the shown portion of `code/analysis/correlations.py` contains no implementation of Benjamini‑Hochberg FDR correction or code that merges all p‑values and writes the corrected results. The task’s core requirement is therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

