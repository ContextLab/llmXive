# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008a` (rejected 1x): The repository contains `code/00_feasibility_check_join.py`, but the script is truncated and shows no logic for loading the RT dataset, checking for the “Simple Reaction Time” task, filtering participants with missing RT data, writing `data/interim/feasibility_exclusion_log.csv`, or creating `data/processed/feasibility_report.md`. Moreover, the required output files `data/interim/joined_metadata.csv`, `data/interim/feasibility_exclusion_log.csv`, and `data/processed/feasibility_report.md` are absent. The task’s core deliverables are therefore not satisfied.
- `T012` (rejected 1x): The repository lacks the required `data/interim/exclusion_log.csv` and `data/interim/behavioral_metrics.csv` files, and the expected output `data/processed/features_clr.csv` is not present. Moreover, `code/03_extract_features.py` is truncated (ends abruptly) and its docstring mentions outputting `data/interim/eeg_psd.csv` instead of the mandated CLR‑transformed feature CSV, indicating the implementation is unfinished.
- `T007` (rejected 1x): The repository contains a `code/01_download_data.py` file, but it is incomplete (truncated, uses placeholder SHA256, does not actually verify task names against the expected set, and never writes `data/interim/detected_tasks.log`). The required log file is missing, so the script does not fulfill the task’s specifications.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

