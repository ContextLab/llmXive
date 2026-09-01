# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The repository lacks both `data/raw/zenodo_10043838.csv` and `data/raw/zenodo_11023456.csv`, so the verification condition of having a non‑empty CSV is unmet. Moreover, `code/ingest.py` is truncated and does not contain logic to try the primary DOI, fall back to the secondary DOI, or raise `DataUnavailableError` as required. The task therefore remains incomplete.
- `T026` (rejected 1x): The repository contains `code/descriptors.py`, but the shown implementation stops after parsing compositions and does not include logic that computes the required descriptors or writes them to `data/processed/descriptors.csv`. Moreover, the file `data/processed/descriptors.csv` is absent, so the verification conditions (existence, non‑empty, required columns) are not satisfied. The next implementer must add the descriptor calculations and ensure the CSV is generated with the specified columns.
- `T033` (rejected 1x): The repository lacks the required input file `data/processed/descriptors.csv` and the expected output `data/processed/correlation_matrix.csv`. Moreover, while `code/analyze.py` defines functions for loading data and computing Pearson/Spearman correlations, it never writes a combined correlation matrix (including p‑values) to the specified CSV, and the file is truncated before any saving logic. The task’s core deliverables are therefore missing.
- `T035` (rejected 1x): The repository lacks the required `data/processed/descriptors.csv` input, the `vif_diagnostic_log.json` output, and the shown portion of `code/analyze.py` does not contain any VIF calculation or logging logic. Consequently the script does not fulfill the exclusion, flagging, and diagnostic‑log requirements. The next implementer must add VIF computation for the three predictors, ensure “weighted mean radius” is excluded, write flags for VIF > 5, and generate the missing log file.
- `T036` (rejected 1x): The repository lacks the required `artifacts/models/best_model.pkl` file, and `artifacts/metrics/stability_metrics.json` does not exist. Moreover, `code/analyze.py` contains only descriptor loading and correlation calculations; it does not perform bootstrapping of feature importance, nor does it write any CI metrics to the expected JSON file. The task’s core functionality and output are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

