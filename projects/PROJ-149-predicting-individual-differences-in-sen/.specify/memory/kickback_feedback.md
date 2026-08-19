# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008a` (rejected 1x): The repository contains `code/00_feasibility_check_join.py`, but the script is truncated and there is no evidence it performs the required join, verification, filtering, logging, or report generation. Crucially, the expected output files `data/interim/joined_metadata.csv`, `data/interim/feasibility_exclusion_log.csv`, and `data/processed/feasibility_report.md` are absent. The next implementer must ensure the script fully implements the join logic, creates the three output files, logs excluded participants, and exits with code 1 on failures.
- `T012` (rejected 1x): The required input file `data/interim/exclusion_log.csv` does not exist, so the script cannot run, and the expected output `data/processed/features_clr.csv` is also missing. Additionally, the verification schema `contracts/feature_schema.schema.yaml` (or `schema.yaml`) is absent, preventing any validation of the output format. These essential artifacts must be present and populated for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

