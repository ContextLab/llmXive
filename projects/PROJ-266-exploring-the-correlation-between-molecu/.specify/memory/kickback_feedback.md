# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The repository lacks the required input file `data/processed/conformers.pkl` and the expected output `data/processed/descriptors_raw.csv`. Moreover, the provided `code/data/descriptors.py` is truncated and does not show the full implementation of loading the conformer file, computing the three variances, or writing the CSV. These essential artifacts are missing, so the task is not genuinely completed.
- `T013` (rejected 1x): The repository contains a partially shown `generate_conformers` function with the required FR‑003 comment, but the required output file `data/processed/conformers.pkl` is absent, indicating the conformer ensembles are never saved. Additionally, the script references `pd` without importing pandas, suggesting the implementation is incomplete. The missing pickle file must be generated for the task to be considered complete.
- `T015` (rejected 1x): The required output file `data/processed/correlation_results.csv` does not exist, and the provided `code/data/analysis.py` snippet shows only data loading and some utility functions—no implementation that computes Pearson/Spearman correlations for each descriptor while controlling for logP, MW, and PSA, nor code that saves the results to the specified CSV. The task’s core requirement is therefore unmet.
- `T028` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/scaling_analysis_results.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

