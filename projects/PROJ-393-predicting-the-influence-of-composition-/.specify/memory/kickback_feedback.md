# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T027` (rejected 1x): The repository contains the preprocessing script, but the required output file `data/processed/alloys_raw.csv` is absent, violating the task’s guarantee that the pipeline must produce this CSV (even for empty data). The missing CSV must be generated and committed.
- `T032` (rejected 1x): The provided `feature_engineering_pipeline.py` contains the loading and descriptor‑calculation logic, but the excerpt ends before any code that writes the resulting DataFrame to `data/processed/alloys_features.csv`. Moreover, the required input file `data/processed/alloys_raw.csv` is absent, so the pipeline cannot be exercised to confirm correct behavior. The implementation must include the step that saves the engineered features and be tested with an actual `alloys_raw.csv` file.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

