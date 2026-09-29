# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016b` (rejected 1x): The script never reads `config/default.yaml` nor extracts a `target_steps` value; it relies solely on a command‑line `--steps` argument with a hard‑coded default. The required fallback warning and use of the config‑derived step count are absent, and the config file itself is missing. The task’s core requirement is therefore not met.
- `T016c` (rejected 1x): The `run_simulation.py` script lacks any verification of reaching `target_steps`, does not apply a “Time‑Bound Baseline” flag, and never writes a Parquet file to `data/raw/baseline_partial.parquet`. Moreover, the required `baseline_partial.parquet` file is missing from the repository. These omissions mean the task’s core requirements are not met.
- `T026b` (rejected 1x): The `run_simulation.py` script never reads a `config.yaml` file, does not load a `target_steps` value, and writes its output to `data/output.json` instead of recording metrics under `data/processed/`. Moreover, the required `config.yaml` file is missing from the repository. These omissions mean the implementation does not meet the stated task requirements.
- `T057` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/validate_metrics.py, data/raw/baseline_partial.parquet

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

