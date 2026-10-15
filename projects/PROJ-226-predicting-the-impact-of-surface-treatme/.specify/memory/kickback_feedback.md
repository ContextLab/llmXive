# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): Requested task execution failed; rerun successfully: code/verify_data_source.py exit=1
- `T005` (rejected 1x): The split outputs are 2/0/1 records (66.67%/0%/33.33%), which violates the required 70/15/15 proportion within 1% tolerance — `val.csv` is empty (header only), and `split_summary.json` itself records `"validation": 0`. Additionally, the script's fallback bypassed FR-011: the log shows all 3 groups were excluded for having <5 records, but the code then reverted to the full dataset, so the exclusion rule was not actually applied. The implementer needs a cleaned dataset with enough records per pair (or must handle the tiny fixture without silently skipping the sparsity filter) so that non-empty,
- `T006` (rejected 1x): The script ran (exit 0, 17 combos ≤ 50) and models plus `grid_search_results.json` exist, but the required 95% bootstrapped CIs are `[NaN, NaN]` for every one of the 17 entries — the validation set contained only 1 record (fallback 80/20 split of a 3-row dataset), so R² is degenerate (0.0 for all models) and the bootstrap CI was never actually computed. The task requires recorded validation R², RMSE, and a real bootstrapped CI; the deliverable needs a validation set with ≥2 (realistically many more) records so meaningful metrics and CIs can be produced.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

