# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T026a` (rejected 1x): The `code/agent/monolithic_runner.py` file is truncated (the `run_monolithic` implementation ends abruptly at “contex”) and thus does not contain a complete, functional `run_monolithic(dataset)` function. Additionally, the required dataset file `data/processed/filtered_tasks.csv` is missing. Both the code and the input data needed to satisfy the task are absent.
- `T026b` (rejected 1x): The `dual_track_runner.py` file is present but the `run_dual_track` function is cut off and not fully implemented. Additionally, the required dataset file `data/processed/filtered_tasks.csv` is missing. Both the functional implementation and the input data are absent, so the task is not satisfied.
- `T026f` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/monolithic_logs.json, data/processed/dual_track_logs.json
- `T008a` (rejected 1x): The provided `code/main.py` stops mid‑implementation (the `wrap_task` method is truncated and no context manager or `resource_monitor_context` is defined), and there is no logic that raises `ResourceLimitExceeded` on threshold breach. Consequently the required wrapper logic and fail‑fast behavior are missing, so the task’s specifications are not satisfied.
- `T030` (rejected 1x): The required input file `data/processed/filtered_tasks.csv` does not exist, so the script cannot compute the sample size, and the expected output `data/processed/power_report.json` was never generated. Without these artifacts the power analysis cannot be performed nor the sufficiency check enforced.
- `T033` (rejected 1x): The repository lacks the required input `data/processed/filtered_tasks.csv` and the expected output `data/processed/annotation_sample.csv`. Moreover, the provided `annotator.py` uses a `progressive_constraints` field and does not clearly implement a CLI that writes the specified columns (`task_id`, `raw_prompt`, `constraint_list`, `constraint_count`) with the stratified sampling logic. Without these files and a complete script, the task’s requirements are not satisfied.
- `T034` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/execution_traces.csv, data/processed/annotation_labels.csv, data/processed/agreement_rate_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

