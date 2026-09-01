# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of a `.project_init.json` file in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` was provided, nor any displayed content matching the required JSON. The implementer must create the file with the exact specified fields and values.
- `T002` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `data/reports/` under `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`) or the `.gitkeep` files within them is provided. The implementer must add these folders and place a `.gitkeep` file in each to satisfy the task.
- `T003` (rejected 1x): No evidence of the required directories (`code/data/`, `code/tests/`, `code/utils/`) or the `__init__.py` files within them is provided; without these artifacts the task is not satisfied.
- `T008` (rejected 1x): The `validation.py` module exists, but the required schema files (`contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`) are missing, and the provided code is truncated so it’s unclear whether it actually validates data against those specific schemas. Without the schemas (or a stub that loads them) the utility cannot fulfill the task’s requirement.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/gdelt_events.csv, data/raw/google_trends.csv
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/aligned_timeseries.csv, data/processed/stationarity_check.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

