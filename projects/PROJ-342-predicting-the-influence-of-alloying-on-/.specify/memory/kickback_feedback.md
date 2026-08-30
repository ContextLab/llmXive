# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The required `data/processed/cleaned_mg.csv` file is absent, and the existing `data/ingestion_stats.json` contains placeholder values (all counts zero, retention rate 0.0), indicating no real ingestion or logging was performed. The task’s core outputs are missing or empty.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: models/best_model.pkl

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

