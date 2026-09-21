# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): The provided `code/download.py` is truncated (e.g., `download_raw_data` ends abruptly) and lacks the required logic to actually download the dataset, generate `data/raw/download_manifest.json`, and create a sample EEG file with a unique run ID. No `data/raw/download_manifest.json` file exists, confirming the script does not fulfill the task’s specifications.
- `T021` (rejected 1x): The repository lacks the required `data/analysis/complexity_metrics.csv` and the expected output `data/analysis/ancova_results.csv`. Moreover, the provided `code/analysis.py` (truncated) shows no implementation of the ANCOVA model using `statsmodels` nor any logic to read `vif_valid_predictors.json` or write the results file. Consequently the task’s specifications are not met.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/analysis/vif_diagnostics.log, data/analysis/vif_valid_predictors.json
- `T026` (rejected 1x): The `code/utils/monitor.py` file exists but never writes a `data/analysis/resource_usage.json` file (the code is truncated and lacks any JSON‑dump logic). Consequently the required output file is missing, so the task’s specification is not met.
- `T028` (rejected 1x): The required artifact `data/analysis/resource_usage.json` does not exist, so there is no evidence that the pipeline runtime was measured or that it meets the ≤ 6 hour limit. The task’s verification step cannot be satisfied without this file.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

