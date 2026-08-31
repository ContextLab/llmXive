# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): The repository lacks the required `default.yaml` and the `data/raw/baseline_partial.parquet` file, and the provided `run_simulation.py` does not accept a `--config` argument nor produce the expected parquet output, so there is no evidence that a 10,000‑step run was performed or that a time‑bound baseline was recorded.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/validate_metrics.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

