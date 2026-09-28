# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T050` (rejected 1x): No updated `loader.py` file is present, nor any log output or test run showing the exact counts and reasons for dropped instances. The required artifact (code change with explicit logging) and verification evidence are missing.
- `T051` (rejected 1x): declared artifact(s) missing/empty/invalid: data/audit_logs/fallbacks.jsonl
- `T052` (rejected 1x): No updated `glm_analyzer.py` file is present, nor any test script that mocks a missing `statsmodels` version and checks for a `RuntimeError`. The required version‑check implementation and verification evidence are missing.
- `T053` (rejected 1x): No code changes adding a `--dry-run` flag to `run_baseline.py`, `run_high_fidelity.py`, or `run_7b_experiments.py` are present, nor are there any execution logs or output files showing the scripts run with `--dry-run` completing in under a minute and writing a subset of processed instances. The required artifacts (modified scripts and verification output) are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

