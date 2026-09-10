# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T023b` (rejected 1x): The provided `experiment_runner.py` does not contain any code that reads `latency_violations.json`, checks the >10% >100 ms condition, adjusts parameters, or writes an abort entry to `data/results/sweep_abort_log.json`. Moreover, the required `sweep_abort_log.json` file is absent. The task’s mitigation logic and abort‑log artifact are therefore missing.
- `T026` (rejected 1x): The integration test file exists, but the required output artifacts are not present: `data/results/final_report.md` is missing, and `data/results/deltas.json` contains only placeholder zero values rather than real comparative results. The task’s requirement to produce these files after running `main.py --compare` is therefore not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

