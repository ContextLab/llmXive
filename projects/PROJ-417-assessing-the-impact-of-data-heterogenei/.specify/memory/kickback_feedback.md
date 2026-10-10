# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): Checked `code/main.py`, `data/results/simulation_raw.json`, and the execution log `code/.tasks/T006.code_run_primary_sweep.py.log`. The JSON file is present but its size (≈75 KB) and the displayed excerpt suggest far fewer than the required 2 500 replicate records, and no count is provided. The log records a run of a different script (`run_primary_sweep.py`) lasting only seconds and does not contain the required runtime or RAM usage information, nor does it show that `code/main.py` was invoked with the full‑sweep parameters. Consequently the task’s quantitative and performance verification req

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

