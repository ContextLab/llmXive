# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/repo_metadata.json
- `T018b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/pr_turnaround.csv
- `T029` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/statistical_results.json
- `T023b` (rejected 1x): The required `data/processed/distribution_stats.json` file does not exist, and the provided `code/analyze.py` (as shown) contains no logic for computing skewness, kurtosis, or Shapiro‑Wilk p‑values nor for writing those results to the specified JSON file. The implementation therefore does not meet the task requirements.
- `T026b` (rejected 1x): No code, script, log file, or test output was provided that shows the p‑value being compared to α=0.05, the appropriate conclusion being logged, or a `SignificanceError` being raised when required. Without any artifact demonstrating this logic, the task is not satisfied.
- `T032` (rejected 1x): No boxplot image, script, or notebook was provided that shows the turnaround‑time‑vs‑PR‑type plot with labeled axes and whiskers defined by IQR bounds, so the requirement cannot be verified as met.
- `T033` (rejected 1x): No `artifacts/boxplot.png` file is present, and there is no evidence of a saved visualization with ≥300 DPI resolution. The required high‑resolution image is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

