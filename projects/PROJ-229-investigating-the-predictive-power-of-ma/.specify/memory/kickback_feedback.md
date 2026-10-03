# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005a` (rejected 1x): The script `code/data/fetch_materials.py` is present, but the required output file `data/raw/materials_project_data.json` does not exist, indicating the data fetch step was never successfully executed. The missing deliverable must be generated (and validated) to satisfy the task.
- `T005b` (rejected 1x): The repository contains the `code/data/fetch_nist_data.py` script, but the required output file `data/raw/nist_data.json` is missing; there is no evidence that the script was executed or that the NIST data was actually fetched. The deliverable specified by the task is therefore not present.
- `T005c` (rejected 1x): The `data/results/target_decision.json` file is empty (`{}`) and the required `data/results/imputation_rate_report.json` does not exist at all, so the script’s outputs do not meet the specification. Additionally, the provided `target_consistency_check.py` is truncated and does not show the full logic needed to compute the correlation, decide the target, and generate the required JSON fields. The missing/empty result files must be created with the specified contents for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

