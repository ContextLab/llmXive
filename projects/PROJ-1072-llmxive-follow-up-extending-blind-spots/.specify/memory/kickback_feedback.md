# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The `code/tune_threshold.py` file is truncated (ends mid‑function) and does not contain the logic to iterate thresholds, compute agreement rates, or write `data/pilot/tuned_threshold.json`. Moreover, the required input `data/pilot/pilot_ground_truth_labels.jsonl` and the expected output `data/pilot/tuned_threshold.json` are both absent. The task’s deliverables are therefore not present.
- `T023` (rejected 1x): No code, script, or logs were presented that implement the required inference loop with `temperature=0.0`, a fixed 10‑minute `signal.alarm` timeout, error logging (ERR_TIMEOUT), and the global 6‑hour runtime guard. The artifact needed to verify the task (e.g., a Python module or execution output) is missing.
- `T023a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/runtime_limit_reached.json
- `T024` (rejected 1x): No code, configuration, or log files were provided showing the added error‑handling logic, JSON‑structured warning logs with the required codes, or the skip‑task behavior. Without these artifacts the claim cannot be verified. The implementer must supply the modified source (e.g., T022 implementation) and example log output demonstrating ERR_TIMEOUT and ERR_EMPTY handling.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

