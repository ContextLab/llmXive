# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): The `pilot_runner.py` file exists but the provided excerpt ends before any code that writes execution time to `data/results/pilot_log.json`, and the required `pilot_log.json` file is absent from the repository. Without a JSON log recording the pilot’s runtime, the task’s core requirement is not met.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
- `T015` (rejected 1x): No code, test, or documentation was presented showing that corrupted‑file handling was added (i.e., logging the error, skipping the realization, and continuing). Without any artifact demonstrating this behavior, the requirement is not satisfied.
- `T023` (rejected 1x): No JSON metadata files were presented in the evidence, and there is no code or output showing that the required `data/metadata/{realization_id}_algo_{name}.json` files are created with the keys `algo_name`, `algo_version`, `exec_time_sec`, and `timestamp`. The implementer’s claim cannot be verified without these artifacts.
- `T024` (rejected 1x): No code, configuration, log files, or documentation were provided that demonstrate the implementation of convergence‑failure handling (logging the failure, recording the gap configuration, and excluding the case from downstream analysis). Without these artifacts, the requirement cannot be verified as met.
- `T026` (rejected 1x): The provided `tests/integration/test_bias_pipeline.py` is truncated and never reaches any assertion that checks for `data/results/bias_summary.csv` or validates its rows. Moreover, the required `bias_summary.csv` file is absent, indicating the test does not actually generate or verify it. The integration test must contain code that runs the full pipeline (or a suitable mini‑pipeline) and then asserts the CSV’s existence and that it contains valid data rows. This is currently missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

