# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The provided `code/ingestion.py` contains synthetic data‑generation logic and never checks for the presence of the required raw files. Moreover, the three expected raw data files (`data/raw/delay_discounting.csv`, `procrastination.csv`, `nback.csv`) are absent from the repository. Hence the ingestion task’s core requirement is not satisfied.
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/harmonized_dataset.parquet, state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

