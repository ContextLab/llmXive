# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): The required `data/processed/merged_data.csv` file is missing, and no evidence of raw artifacts saved in `data/raw/` is provided, even though the `.ready` marker file exists. Both required output files must be present for the task to be considered complete.
- `T026` (rejected 1x): declared artifact(s) missing/empty/invalid: code/visual_metrics.py
- `T031` (rejected 1x): The required data file `data/processed/final_analysis_data.csv` is missing, so the analysis cannot be run. `code/03_analysis.py` does not implement the VIF‑based conditional logic nor use `scipy.stats.linregress` for linear regression, and it never writes a JSON with the required keys (`r`, `p`, `beta`, `ci_lower`, `ci_upper`). The existing `results/statistics/statistics.json` contains a different schema (no beta or confidence intervals). These gaps must be fixed for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

