# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): The submission provides no visible modifications to `fetch_gdelt.py` or `fetch_google_trends.py`, nor any logs, tests, or documentation showing retry logic and non‑zero exit on failure. Without the actual script changes or evidence that the error‑handling behavior works, the task requirement is not satisfied.
- `T018` (rejected 1x): No `preprocess.py` file or code snippet was provided showing an Augmented Dickey‑Fuller test and iterative differencing logic; without the actual implementation we cannot confirm the requirement was met. The missing artifact is the preprocessing script containing the ADF test and automatic differencing until stationarity.
- `T019` (rejected 1x): No `preprocess.py` file or code snippet was provided, and there is no evidence that z‑score normalization after stationarity testing has been implemented. The required artifact is missing, so the task is not satisfied.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/aligned_timeseries.csv, data/processed/stationarity_check.csv
- `T022` (rejected 1x): No artifact (e.g., updated `preprocess.py` containing a post‑interpolation completeness check) was provided; the claim lacks any code, tests, or documentation demonstrating that such a check was implemented. The required implementation is therefore missing.
- `T026` (rejected 1x): No evidence of an `analyze.py` file containing a Granger causality implementation was provided; the claim lacks any code, function, or test output demonstrating the required statistical test. The required artifact is missing.
- `T027` (rejected 1x): No `analyze.py` file or code implementing sensitivity analysis was provided; the evidence contains no artifacts, outputs, or documentation showing that the required analysis was added. The task’s core deliverable is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

