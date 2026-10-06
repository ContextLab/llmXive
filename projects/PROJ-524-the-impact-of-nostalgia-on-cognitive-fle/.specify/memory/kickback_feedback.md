# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): The required input file `data/processed/final_cleaned_dataset.csv` is missing, so the analysis cannot actually run on real data. Moreover, the generated `statistical_report.json` does not contain the top‑level keys `p_values` and `t_statistics` as specified (it uses a different structure and even references a different task ID). The implementation therefore does not satisfy the task’s requirements.
- `T027b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset_no_mmse.csv, data/results/robustness_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

