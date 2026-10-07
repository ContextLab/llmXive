# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T042` (rejected 1x): The provided `code/robustness.py` contains a `check_collinearity_flag` function but the rest of the script (including the logic that would skip the calculation and write `status: 'skipped'` to `data/results/partial_corr.json`) is truncated and not present. Moreover, the required `data/results/partial_corr.json` file does not exist, indicating the skipping behavior was never executed. The task’s core requirement—to dynamically read the flag and, when true, write a “skipped” status file—is therefore not fulfilled.
- `T044` (rejected 1x): The repository contains a `log_exclusion` helper that writes to `data/logs/exclusions.log`, but the log file is absent and the ingestion script never reaches the exclusion logic (it raises `NotImplementedError` for data loading). Consequently no actual exclusions are logged, and the required numeric threshold values are never recorded. The task’s requirement is therefore not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

