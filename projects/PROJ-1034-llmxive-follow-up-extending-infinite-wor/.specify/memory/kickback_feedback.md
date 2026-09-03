# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016b` (rejected 1x): The provided `run_simulation.py` does not read `config/default.yaml`, runs only the user‑specified number of steps (default 100) and lacks any check for a minimum of 10,000 steps. It also never flags a “Time‑Bound Baseline” nor writes a Parquet file to `data/raw/baseline_partial.parquet`. Moreover, the required `config/default.yaml` and the expected output Parquet file are missing from the repository.
- `T057` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/validate_metrics.py, data/raw/baseline_partial.parquet

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

