# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The repository contains a partially‑implemented `generate_synthetic.py` (the file ends abruptly inside `writer.writerow` and never calls the generation function), and the required output file `data/raw/synthetic_traces.csv` does not exist. The task’s core deliverable—producing a deterministic CSV of synthetic traces—is therefore missing.
- `T014` (rejected 1x): The repository contains `code/analysis/environment.py`, which defines functions for recording environmental parameters and raises `ConfigurationError` when `barometric_pressure_hPa` is missing, but it does not include any logic that writes these records to `data/processed/environment_logs.json`. Moreover, the required `environment_logs.json` file is absent from the `data/processed` directory. The core output requirement of the task is therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

