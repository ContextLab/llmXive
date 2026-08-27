# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020` (rejected 1x): The provided `03_correlation_analysis.py` stops after a partially shown `compute_pearson_with_correction` function and does not contain implementations for lag‑window analysis, bootstrap resampling (1000 iterations, seed = 42), Newey‑West standard errors, FDR correction, SNR calculation, or writing the required `data/processed/correlation_results.csv` with a `region_type` column. Moreover, the expected output CSV file is absent from the repository. These missing components mean the task’s core requirements are not satisfied.
- `T040` (rejected 1x): The required input `data/processed/merged_monthly.csv` and `docs/runtime_profile.md` are missing, and the produced `docs/runtime_report.md` contains only placeholder values (zero duration, zero CPU/memory) with a note to run the script on real data. No genuine runtime measurement was performed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

