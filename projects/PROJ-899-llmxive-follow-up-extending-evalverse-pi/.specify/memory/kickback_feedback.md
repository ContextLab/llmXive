# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`src/`, `tests/`, `specs/`) is provided; the claim lacks any artifact showing that the project structure has been created. The implementer must add and show these folders (with at least placeholder files) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or CI scripts invoking `ruff`/`black`) were presented, nor any evidence that these tools are installed or run. The required artifacts to demonstrate that linting and formatting are configured are missing.
- `T024` (rejected 1x): The repository contains a partially‑implemented `src/models/evaluate.py` (the `calculate_inference_time_projection` function is truncated and no code writes `timing_profile.csv`). Moreover, the required output file `data/timing_profile.csv` does not exist. Consequently the per‑clip inference time calculation and projected total‑hours output are not actually produced.
- `T023b` (rejected 1x): The `src/data/profiles.py` file is incomplete (the `save_profiling_results` function is truncated and never writes to `data/profiling_logs.json`), and the required output file `data/profiling_logs.json` does not exist. Consequently, the task’s requirement to log exact CPU time and memory peak to a JSON file is not fulfilled.
- `T025` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/feasibility_profile.json
- `T026#1` (rejected 1x): The repository lacks the required `data/sensitivity_sweep_raw.csv` file, and the `run_threshold_sweep` function in `src/models/metrics.py` is truncated before completing the logic and writing the CSV. The threshold sweep output and CSV generation are therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

